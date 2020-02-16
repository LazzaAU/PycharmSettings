from typing import Optional

from pocketsphinx import Decoder

from core.asr.model.ASR import ASR
from core.asr.model.ASRResult import ASRResult
from core.asr.model.Recorder import Recorder
from core.util.Stopwatch import Stopwatch


class PocketSphinxASR(ASR):
	NAME = 'Pocketsphinx ASR'


	def __init__(self):
		super().__init__()
		self._capableOfArbitraryCapture = True
		self._isOnlineASR = False
		self._decoder: Optional[Decoder] = None


	def onStart(self):
		super().onStart()
		config = Decoder.default_config()
		config.set_string('-hmm', f'{self.Commons.rootDir()}/venv/lib/python3.7/site-packages/pocketsphinx/model/en-us')
		config.set_string('-lm', f'{self.Commons.rootDir()}/venv/lib/python3.7/site-packages/pocketsphinx/model/en-us.lm.bin')
		config.set_string('-dict', f'{self.Commons.rootDir()}/venv/lib/python3.7/site-packages/pocketsphinx/model/cmudict-en-us.dict')
		self._decoder = Decoder(config)


	def decodeStream(self, recorder: Recorder) -> ASRResult:
		super().decodeStream(recorder)

		self._decoder.start_utt()
		inSpeech = False
		result = None

		with Stopwatch() as processingTime:
			for chunk in recorder.generator():
				if self._timeout.isSet() or not chunk:
					break

				self._decoder.process_raw(chunk, False, False)
				if self._decoder.get_in_speech() != inSpeech:
					inSpeech = self._decoder.get_in_speech()
					if not inSpeech:
						self._decoder.end_utt()
						result = self._decoder.hyp() if self._decoder.hyp() else None
						break

			self.end(recorder)

		return ASRResult(
			text=result.hypstr.strip(),
			session=recorder.session,
			likelihood=self._decoder.hyp().prob,
			processingTime=processingTime.time
		) if result else None