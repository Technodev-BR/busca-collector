"""Coletor de imóveis do Busca-Busca.

Pipeline: download -> parse -> normalize -> enviar para a API de ingestão do backend.
O coletor NÃO escreve direto no banco (ver docs/servicos/collector-python.md e ADR-0001).
"""

__version__ = "0.1.0"
