from . import CheeseCog, MentionCog, AudioCog

class CogFactory():
    def __init__(self, bot: 'cheesebot.CheeseBot') -> None:
        self.__bot = bot
        self.__factories = {
            AudioCog: self.__create_audio_cog,
            MentionCog: self.__create_mention_cog,
        }

    def __call__(self, cog_type: type) -> CheeseCog:
        return self.__factories[cog_type]()

    def __create_audio_cog(self) -> AudioCog:
        from .audio import SEPicker
        return AudioCog(
            self.__bot,
            voice_channel=self.__bot.config['voice_channel'],
            bgm='{}/bgm/stream.raw'.format(self.__bot.data_path),
            se_picker=SEPicker('{}/se'.format(self.__bot.data_path))
        )

    def __create_mention_cog(self) -> MentionCog:
        from .cogs import PhrasePicker
        return MentionCog(self.__bot, PhrasePicker(self.__bot.db.table('phrases')))
