# SimplyType

A cross-platform typing game with a clean GUI interface.

## Features

- different game modes
- game statistics
- theme and language customization
- user-uploaded word sets

## Usage

- Clone the repository and set working directory to 'speed-typing-game'
- Create a virtual environment and install required dependencies:

    ```console
    pip install -r requirements.txt
    ```

- run the application:

    ```console
    python3 .\speed_typing_game.py
    ```

## Adding translations

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
