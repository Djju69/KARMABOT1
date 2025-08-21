from dataclasses import dataclass

@dataclass
class Bots:
    bot_token: str
    admin_id: int

@dataclass
class Settings:
    bots: Bots

settings = Settings(
    bots=Bots(
        bot_token="8201307288:AAHB0hdPKXLsd0a6MR4klgtNEM5p46kEmr4",
        admin_id=6391215556
    )
)
