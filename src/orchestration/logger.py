"""
Structured Logging for EideticRAG
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import json
import traceback
from loguru import logger
import sys


class StructuredLogger:
    """Structured logging with Loguru"""
    
    def __init__(
        self,
        log_dir: Optional[Path] = None,
        log_level: str = "INFO",
        enable_console: bool = True,
        enable_file: bool = True
    ):
        """
        Initialize structured logger
        
        Args:
            log_dir: Directory for log files
            log_level: Logging level
            enable_console: Enable console output
            enable_file: Enable file output
        """
        self.log_dir = Path(log_dir) if log_dir else Path("./logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Remove default logger
        logger.remove()
        
        # Add console handler
        if enable_console:
            logger.add(
                sys.stdout,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                level=log_level,
                colorize=True
            )
        
        # Add file handlers
        if enable_file:
            # General log file
            logger.add(
                self.log_dir / "eidetic_rag_{time:YYYY-MM-DD}.log",
                rotation="1 day",
                retention="30 days",
                level=log_level,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
                serialize=False
            )
            
            # JSON structured log for analysis
            logger.add(
                self.log_dir / "structured_{time:YYYY-MM-DD}.json",
                rotation="1 day",
                retention="7 days",
                level=log_level,
                serialize=True
            )
            
            # Error log
            logger.add(
                self.log_dir / "errors_{time:YYYY-MM-DD}.log",
                rotation="1 day",
                retention="30 days",
                level="ERROR",
                backtrace=True,
                diagnose=True
            )
        
        self.logger = logger
    
    def log_query(
        self,
        query: str,
        intent: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Log a user query
        
        Args:
            query: Query text
            intent: Classified intent
            metadata: Additional metadata
        
        Returns:
            Query ID for tracking
        """
        query_id = self._generate_query_id()
        
        self.logger.info(
            f"Query received",
            query_id=query_id,
            query=query[:200],  # Truncate for logging
            intent=intent,
            metadata=metadata or {}
        )
        
        return query_id
    
    def log_retrieval(
        self,
        query_id: str,
        num_chunks: int,
        strategy: str,
        duration_ms: float,
        metadata: Optional[Dict] = None
    ):
        """Log retrieval operation"""
        self.logger.info(
            f"Retrieval completed",
            query_id=query_id,
            num_chunks=num_chunks,
            strategy=strategy,
            duration_ms=duration_ms,
            metadata=metadata or {}
        )
    
    def log_generation(
        self,
        query_id: str,
        model: str,
        tokens_used: int,
        duration_ms: float,
        metadata: Optional[Dict] = None
    ):
        """Log generation operation"""
        self.logger.info(
            f"Generation completed",
            query_id=query_id,
            model=model,
            tokens_used=tokens_used,
            duration_ms=duration_ms,
            metadata=metadata or {}
        )
    
    def log_reflection(
        self,
        query_id: str,
        verdict: str,
        hallucination_score: float,
        iterations: int,
        metadata: Optional[Dict] = None
    ):
        """Log reflection operation"""
        level = "WARNING" if hallucination_score > 0.3 else "INFO"
        
        self.logger.log(
            level,
            f"Reflection completed",
            query_id=query_id,
            verdict=verdict,
            hallucination_score=hallucination_score,
            iterations=iterations,
            metadata=metadata or {}
        )
    
    def log_memory_operation(
        self,
        operation: str,
        memory_id: str,
        success: bool,
        metadata: Optional[Dict] = None
    ):
        """Log memory operation"""
        level = "INFO" if success else "ERROR"
        
        self.logger.log(
            level,
            f"Memory {operation}",
            memory_id=memory_id,
            success=success,
            metadata=metadata or {}
        )
    
    def log_error(
        self,
        error: Exception,
        context: str,
        metadata: Optional[Dict] = None
    ):
        """Log error with context"""
        self.logger.error(
            f"Error in {context}",
            error_type=type(error).__name__,
            error_message=str(error),
            traceback=traceback.format_exc(),
            metadata=metadata or {}
        )
    
    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        success: bool,
        metadata: Optional[Dict] = None
    ):
        """Log performance metrics"""
        level = "INFO" if duration_ms < 1000 else "WARNING"
        
        self.logger.log(
            level,
            f"Performance: {operation}",
            duration_ms=duration_ms,
            success=success,
            metadata=metadata or {}
        )
    
    def log_cache_hit(
        self,
        cache_type: str,
        key: str,
        hit: bool
    ):
        """Log cache hit/miss"""
        self.logger.debug(
            f"Cache {'hit' if hit else 'miss'}",
            cache_type=cache_type,
            key=key[:32],  # Truncate key
            hit=hit
        )
    
    def log_api_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: float,
        metadata: Optional[Dict] = None
    ):
        """Log API request"""
        level = "INFO" if status_code < 400 else "ERROR"
        
        self.logger.log(
            level,
            f"API request: {method} {endpoint}",
            status_code=status_code,
            duration_ms=duration_ms,
            metadata=metadata or {}
        )
    
    def get_query_logs(
        self,
        query_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Retrieve logs for a specific query
        
        Args:
            query_id: Query ID to search for
            start_time: Start time filter
            end_time: End time filter
        
        Returns:
            List of log entries
        """
        # This would typically query the structured JSON logs
        # For now, return empty list
        return []
    
    def _generate_query_id(self) -> str:
        """Generate unique query ID"""
        import uuid
        return str(uuid.uuid4())[:16]
