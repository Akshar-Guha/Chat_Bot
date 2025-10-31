"""
CLI utility for core operations
"""

import click
from pathlib import Path

from .ingestor import DocumentIngestor
from .chunker import TextChunker
from .embeddings import EmbeddingGenerator
from .vector_index import VectorIndex


@click.group()
def cli():
    """EideticRAG Core CLI"""
    pass


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--index-dir', type=click.Path(), default='./index',
              help='Index directory')
@click.option('--chunk-size', type=int, default=500,
              help='Chunk size in characters')
@click.option('--chunk-overlap', type=int, default=50,
              help='Chunk overlap in characters')
def ingest(file_path: str, index_dir: str, chunk_size: int, chunk_overlap: int):
    """Ingest a document into the index"""
    
    file_path = Path(file_path)
    index_dir = Path(index_dir)
    
    click.echo(f"Ingesting {file_path.name}...")
    
    # Initialize components
    ingestor = DocumentIngestor()
    chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    embedder = EmbeddingGenerator(cache_dir=index_dir / 'embeddings_cache')
    index = VectorIndex(persist_dir=index_dir)
    
    # Ingest document
    doc = ingestor.ingest(file_path)
    click.echo(f"✓ Document ingested: {doc.doc_id}")
    
    # Chunk document
    chunks = chunker.chunk_document(doc.doc_id, doc.content, doc.metadata)
    click.echo(f"✓ Created {len(chunks)} chunks")
    
    # Generate embeddings
    embedded_chunks = embedder.embed_chunks(chunks)
    click.echo("✓ Generated embeddings")
    
    # Add to index
    count = index.add_embeddings(embedded_chunks)
    click.echo(f"✓ Added {count} chunks to index")
    
    # Persist
    index.persist()
    click.echo("✓ Index persisted")


@cli.command()
@click.option('--index-dir', type=click.Path(), default='./index',
              help='Index directory')
def reindex(index_dir: str):
    """Rebuild the index from scratch"""
    
    index_dir = Path(index_dir)
    
    click.echo("Rebuilding index...")
    
    # Clear existing index
    index = VectorIndex(persist_dir=index_dir)
    index.clear_index()
    
    click.echo("✓ Index cleared")
    click.echo("Run 'ingest' command to add documents")


@cli.command()
@click.option('--index-dir', type=click.Path(), default='./index',
              help='Index directory')
def inspect(index_dir: str):
    """Inspect index contents"""
    
    index_dir = Path(index_dir)
    
    # Load index
    index = VectorIndex(persist_dir=index_dir)
    
    # Get stats
    stats = index.get_stats()
    
    click.echo("\n=== Index Statistics ===")
    click.echo(f"Collection: {stats['collection_name']}")
    click.echo(f"Total Chunks: {stats['total_chunks']}")
    click.echo(f"Embedding Space: {stats['embedding_space']}")


@cli.command()
@click.argument('query')
@click.option('--index-dir', type=click.Path(), default='./index',
              help='Index directory')
@click.option('--k', type=int, default=5, help='Number of results')
def search(query: str, index_dir: str, k: int):
    """Search the index"""
    
    index_dir = Path(index_dir)
    
    # Initialize components
    embedder = EmbeddingGenerator(cache_dir=index_dir / 'embeddings_cache')
    index = VectorIndex(persist_dir=index_dir)
    
    # Generate query embedding
    query_embedding = embedder.embed_text(query)
    
    # Search
    results = index.search(query_embedding, k=k)
    
    click.echo(f"\n=== Search Results for: '{query}' ===\n")
    
    for i, result in enumerate(results, 1):
        click.echo(f"{i}. Score: {result['score']:.3f}")
        click.echo(f"   Chunk ID: {result['chunk_id']}")
        click.echo(f"   Doc ID: {result['metadata']['doc_id']}")
        click.echo(f"   Text: {result['text'][:200]}...")
        click.echo()


if __name__ == "__main__":
    cli()
