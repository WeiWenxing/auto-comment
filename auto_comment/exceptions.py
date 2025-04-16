class AutoCommentError(Exception):
    """Base exception for auto_comment library."""
    pass

class ContentExtractionError(AutoCommentError):
    """Raised when content extraction fails."""
    pass

class CommentGenerationError(AutoCommentError):
    """Raised when comment generation fails."""
    pass

class CommentError(AutoCommentError):
    """Raised when comment sending fails."""
    pass