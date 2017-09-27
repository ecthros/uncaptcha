# uncaptcha

Defeating Google's audio reCaptcha system with 85% accuracy. ![uncaptcha](https://user-images.githubusercontent.com/14065974/30930456-c2cf7e0a-a38f-11e7-869e-d7aa783e6f02.gif)

## Inspiration

Across the Internet, hundreds of thousands of sites rely on Google's reCaptcha system for defense against bots (in fact, Devpost uses reCaptcha when creating an new account). After a Google research team demonstrated a near [complete defeat](https://pdfs.semanticscholar.org/ceef/94e5e9b6188e9aca558efcf92e57ec987bc4.pdf) of the text reCaptcha in 2012, the reCaptcha system evolved to rely on audio and image challenges, historically more difficult challenges for automated systems to solve. Google has continually iterated on its design, releasing a newer and more powerful version as recently as just this year. Successfully demonstrating a defeat of this captcha system would spell significant vulnerability for a huge number of popular sites. 

## What it does

Our unCaptcha system has attack capabilities written for the audio captcha. Using browser automation software, we can interact with the target website and engage with the captcha, parsing out the necessary elements to begin the attack. We rely primarily on the audio captcha attack - by properly identifying spoken numbers, we can pass the reCaptcha programmatically and fool the site into thinking our bot is a human. Specifically, unCaptcha targets the popular site Reddit by going through the motions of creating a new user, although unCaptcha stops before creating the user to mitigate the impact on Reddit.

#### Background

Google's reCaptcha system uses an advanced risk analysis system to determine programmatically how likely a given user is to be a human or a bot. It takes into account your cookies (and by extension, your interaction with other Google services), the speed at which challenges are solved, mouse movements, and (obviously) how successfully you solve the given task. As the system gets increasingly suspicious, it delivers increasingly difficult challenges, and requires the user to solve more of them. Researchers have already identified minor weaknesses with the reCaptcha system - 9 days of legitimate (ish) interaction with Google's services is usually enough to lower the system's suspicion level significantly.

#### Audio
The format of the audio captcha is a varied-length series of numbers spaced out read aloud at varied speeds, pitches, and accents through background noise. To attack this captcha, the audio payload is identified on the page, downloaded, and automatically split by locations of speech. From there, each number audio bit is uploaded to 6 different audio transcription services (IBM, Google Cloud, Google Speech Recognition, Sphinx, Wit-AI, Bing Speech Recognition), and these results are collected. We ensemble the results from each of these to probabilistically enumerate the most likely string of numbers with a predetermined heuristic. These numbers are then organically typed into the captcha, and the captcha is completed. From testing, we have seen 92%+ accuracy in individual number identification, and 85%+ accuracy in defeating the audio captcha in its entirety. 

## Installation

First, install python dependencies:
```
$ pip install -r requirements.txt
```

Make sure you also have sox, ffmpeg, and selenium installed! 
```
$ apt-get install sox ffmpeg selenium
```

Then, to kick off the PoC:

```
$ python main.py
``` 

This opens reddit.com, interacts with the page to go to account signup, generates a fake username, email, password, and then attacks the audio captcha. Once the captcha is completed (whether it passed or not), the browser exits. 

## Paper

Please read our paper, located [here](https://www.usenix.org/system/files/conference/woot17/woot17-paper-bock.pdf), for more information. Additionally, you can visit our website [here](http://uncaptcha.cs.umd.edu/).

## Disclaimer

This is by no means intended to be a working model. unCaptcha was originally intended to be a proof of concept. A number of new protections have been put in place and this code has been modified so that unCaptcha will no longer work.

Although Google has since changed its code so that this attack will no longer work, it is worth noting that it is probably still possible to create a defeat of Google's current ReCaptcha. Therefore, much of this code has been slightly changed, and will certainly no longer work. Please be careful when doing research in this field and responsibly disclose any potential vulnerabilities to Google immediately.

Google has also improved their code such that browser automation will be detected. This means that Selenium cannot be used in its current state to get captchas from Google. This may lead to Google sending odd audio segments back to the end user.

Additionally, we have removed our API keys from all the necessary queries. If you are looking to recreate some of the work or are doing your own research in this area, you will need to acquire API keys from each of the six services used. These keys are delineated in our files by a long string of the character 'X'. 

## Contributors

[Kkevsterrr](https://github.com/Kkevsterrr)

[dpatel19](https://github.com/dpatel19)

[ecthros](https://github.com/ecthros)

[Dave Levin](https://www.cs.umd.edu/~dml/)
