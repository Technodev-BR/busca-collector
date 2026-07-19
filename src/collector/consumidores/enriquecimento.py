"""Consumidor RabbitMQ do enriquecimento (Fase 2).

Consome a fila ``imoveis.enriquecimento`` (eventos ``imovel.enriquecer`` publicados pelo backend).
Para cada mensagem: baixa o detalhe, parseia e envia a POST .../detalhe.

Regras de ack:
- sucesso ou imóvel indisponível/anomalia de parse -> **ack** (não reprocessa em loop; a DLQ é
  para falhas transitórias que esgotaram retry).
- falha transitória (rede/5xx) após esgotar os retries do tenacity -> **nack sem requeue** (vai à
  DLQ configurada no backend), para inspeção.

Modo **opt-in**: o coletor CSV continua sem depender de RabbitMQ. Só o consumidor precisa de pika.
"""
from __future__ import annotations

import argparse
import json
import sys
import time

import pika

from ..config import Settings, get_settings
from ..enriquecimento import enriquecer_imovel
from ..envio.api_client import ErroIngestao, IngestClient
from ..fontes.caixa.detalhe import AnomaliaParse, ImovelIndisponivel
from ..logging import configure_logging, get_logger

log = get_logger("collector.consumer")


def _conexao(settings: Settings) -> pika.BlockingConnection:
    credenciais = pika.PlainCredentials(settings.rabbitmq_user, settings.rabbitmq_password)
    parametros = pika.ConnectionParameters(
        host=settings.rabbitmq_host,
        port=settings.rabbitmq_port,
        credentials=credenciais,
        heartbeat=60,
        blocked_connection_timeout=30,
    )
    return pika.BlockingConnection(parametros)


def _extrair_codigo(body: bytes) -> tuple[str | None, str]:
    try:
        envelope = json.loads(body)
    except json.JSONDecodeError:
        return None, "caixa"
    data = envelope.get("data") if isinstance(envelope, dict) else None
    if not isinstance(data, dict):
        return None, "caixa"
    codigo = data.get("codigo")
    fonte = data.get("fonte") or "caixa"
    return (str(codigo) if codigo else None), str(fonte)


def consumir(settings: Settings) -> None:
    conexao = _conexao(settings)
    canal = conexao.channel()
    canal.queue_declare(queue=settings.rabbitmq_queue_enriquecimento, durable=True, passive=False)
    canal.basic_qos(prefetch_count=settings.rabbitmq_prefetch)

    client = IngestClient(settings)
    client.verificar_api_disponivel()

    def callback(ch, method, _props, body):  # noqa: ANN001 - assinatura do pika
        codigo, fonte = _extrair_codigo(body)
        if not codigo:
            log.warning("consumer.msg_invalida")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        try:
            enriquecer_imovel(codigo, settings, client, fonte)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except ImovelIndisponivel:
            log.warning("consumer.indisponivel", codigo=codigo)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except AnomaliaParse as e:
            log.error("consumer.anomalia_parse", codigo=codigo, erro=str(e))
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except ErroIngestao as e:
            log.error("consumer.erro_ingestao", codigo=codigo, erro=str(e))
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:  # noqa: BLE001 - transitório esgotado -> DLQ
            log.error("consumer.transitorio", codigo=codigo, erro=str(e), tipo=type(e).__name__)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        finally:
            time.sleep(settings.detalhe_pausa_seg)

    canal.basic_consume(queue=settings.rabbitmq_queue_enriquecimento, on_message_callback=callback)
    log.info("consumer.iniciado", fila=settings.rabbitmq_queue_enriquecimento)
    try:
        canal.start_consuming()
    except KeyboardInterrupt:
        log.info("consumer.encerrando")
    finally:
        client.close()
        conexao.close()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="collector-enriquecer",
        description="Consumidor de enriquecimento (detalhe) via RabbitMQ.",
    )
    ap.add_argument("--codigo", help="Enriquece um único imóvel (modo avulso, sem RabbitMQ)")
    ap.add_argument("--fonte", default="caixa")
    ap.add_argument("--log-level", default="INFO")
    ap.add_argument("--json-logs", action="store_true")
    ap.add_argument("--insecure", action="store_true", help="Ignora verificação TLS")
    args = ap.parse_args(argv)

    configure_logging(level=args.log_level, json_logs=args.json_logs)
    settings = get_settings()
    if args.insecure:
        settings.verify_tls = False

    try:
        if args.codigo:
            from ..enriquecimento import enriquecer_avulso

            status = enriquecer_avulso(args.codigo, settings, args.fonte)
            log.info("enriquecimento.avulso", codigo=args.codigo, status=status)
            return 0 if status != "falha" else 1
        consumir(settings)
        return 0
    except Exception as e:  # noqa: BLE001 - fronteira da CLI
        log.error("consumer.falhou", erro=str(e), tipo=type(e).__name__)
        return 1


if __name__ == "__main__":
    sys.exit(main())
