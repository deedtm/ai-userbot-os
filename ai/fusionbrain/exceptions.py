class ArtistException(BaseException):
    def __init__(self):
        """AIArtist exception
        """
        pass


class APIDisabled(ArtistException):
    def __str__(self) -> str:
        return "FusionBrain API disabled"


class FailedGeneration(ArtistException):
    def __init__(self, error_desc: str):
        self.error_desc = error_desc
        
    def __str__(self, error_desc: str) -> str:
        return f"Generation was failed. Error description: {self.error_desc}"
    