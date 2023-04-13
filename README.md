# SimplyType

A cross-platform typing game with a clean GUI interface.

![main window](https://github.com/mboiar/speed-typing-game/blob/main/screenshots/modes.png?raw=true)

## Features

- scalable SQLite-based storage with fast access
- appealing interface based on CSS stylesheets
- different game modes
- game statistics and long-term user statistics
- styling and language customization
- a variety of word sets in different languages and user-uploaded word sets
- persistent user settings across sessions

## Modes

### Learning mode

- Unlimited time
- Cannot proceed further until correct character is typed in
- Summary with  the most frequently incorrectly typed characters, wpm etc.

![learning mode gameplay gif](https://github.com/mboiar/speed-typing-game/blob/main/screenshots/learningmode.gif?raw=true)

### Challenge mode

- Limited time (choose from 30 s, 1 min, etc)
- Incorrectly typed characters are highlighted in real time
- Summary with the most frequently incorrectly typed characters, wpm etc.

![challenge mode gameplay gif](https://github.com/mboiar/speed-typing-game/blob/main/screenshots/challengemode.gif?raw=true)

### Zen mode

- Unlimited time
- Type anything you like
- Relax

![zen mode gameplay gif](https://github.com/mboiar/speed-typing-game/blob/main/screenshots/zenmode.gif?raw=true)



## Usage

For Windows platform, there is an installer available in the latest release.

There is a small possibility that in the future installers for other platforms will be added. Until then, for Unix system users:

- Clone the repository and set working directory to 'speed-typing-game'
- Create a virtual environment and install required dependencies:

    ```console
    pip install -r requirements.txt
    ```

- install `pyinstaller` package with pip and run:

    ```console
    pyinstaller .\speed_typing_game.spec
    ```

## Contributing color schemes

Place a JSON file with color names and values (see examples in the repository) in a subdirectory `resources/styles/[theme]/[color-scheme-name]`, where `theme` is either `dark` or `light` depending on your colors and `color-scheme-name` is the name of your color scheme. Then create a pull request.

## Contributing translations

To translate the application into a new language using PyQt tools, do the following:

- In a virtual environment, run

    ```console
    pip install pyqt6==6.0.2 pyqt6-tools==6.0.2.3.2
    ```

- Clone the repository and set working directory to 'speed-typing-game'
- run `pylupdate` to create a new translation file, where [locale] is the locale code for the target language:

    ```console
    pylupdate . -ts .\speed_typing_game\resources\translate\[locale].ts
    ```

- run `linguist` and complete translations or simply edit XML-based .ts files
- run `lrelease` to generate a .qm file
- done!

On Windows, you should find executables `linguist` and `lrelease` in `{virtual_environment_path}\Lib\site-packages\qt6_applications\Qt\bin` and `pylupdate` in `{virtual_environment_path}\Scripts`
