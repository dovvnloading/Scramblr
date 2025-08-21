
# Scramblr

[![License: MIT](https://img.shields.io/github/license/dovvnloading/Scramblr)](https://github.com/dovvnloading/Scramblr/blob/main/LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.8+-blue.svg?logo=python)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-PySide6-blueviolet.svg?logo=qt)](https://www.qt.io/qt-for-python)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](https://en.wikipedia.org/wiki/Desktop_environment)

A simple, modern desktop utility for safely randomizing image filenames in a directory.

---

## About The Project

Scramblr is a small, focused desktop application built to solve one specific problem: renaming a large number of image files in a folder to a randomized, sequential order. It was developed as a quick-build tool to fulfill a personal need for organizing image datasets without complex software.

The application uses a two-phase renaming process to avoid file-collision errors, ensuring that the operation is safe and reliable even with thousands of files. Its clean, dark-themed interface is designed to be straightforward and easy to use.

If you have ever needed a simple tool to do this one task, I hope Scramblr can help you too.


![Untitled video - Made with Clipchamp (4)](https://github.com/user-attachments/assets/b8f74d5f-c864-4f56-8b4e-f2456fdac3e2)

---

<img width="552" height="432" alt="Screenshot 2025-08-21 070534" src="https://github.com/user-attachments/assets/097fd164-3a0d-400d-9849-0381fd2a2a48" />


---

<img width="486" height="160" alt="Screenshot 2025-08-21 070550" src="https://github.com/user-attachments/assets/a8ecae24-fddf-4b75-8354-de41e1031e21" />

---

<img width="334" height="135" alt="Screenshot 2025-08-21 070604" src="https://github.com/user-attachments/assets/bd21dfd6-7f8f-4b9c-be5b-0d4d16ab9358" />

---


## Features

*   **Folder Selection**: Easily browse and select the target directory.
*   **Custom Filename Prefix**: Define a custom prefix (e.g., `photo_`, `scan_`) for the new filenames.
*   **Safe Two-Phase Renaming**: All files are first renamed to temporary unique IDs before being renamed to their final sequential names, preventing conflicts.
*   **Non-Blocking Operation**: A background worker thread handles the file operations, so the application remains responsive.
*   **Real-time Progress**: A status label and progress bar keep you informed of the process.
*   **Modern Dark Theme**: A custom stylesheet provides a consistent dark theme for all UI elements, including the window title bar on Windows.

## Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

You will need Python 3.8+ and pip installed on your system.

### Installation

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/dovvnloading/Scramblr.git
    ```

2.  **Navigate to the project directory:**
    ```sh
    cd Scramblr
    ```

3.  **(Recommended) Create and activate a virtual environment:**
    ```sh
    # On Windows
    python -m venv venv
    .\venv\Scripts\activate

    # On macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

4.  **Install the required dependencies:**
    The only major dependency is PySide6.
    ```sh
    pip install PySide6
    ```

### Running the Application

Once the dependencies are installed, you can run the application with the following command:

```sh
python main.py
```
*(Assuming you have named the main script `main.py`)*

## How to Use

1.  Launch the application.
2.  Click the **Browse...** button to select a folder that contains your image files.
3.  (Optional) Change the text in the **New Filename Prefix** field to your desired prefix.
4.  Click the **Randomize Files** button.
5.  A confirmation dialog will appear. Click **Yes** to proceed.
6.  The application will process the files, and the progress bar will show the status.
7.  A success message will appear upon completion.

## License

Distributed under the MIT License. See the `LICENSE` file for more information.

---

This project was created to solve a problem quickly and efficiently. It is not intended to be a large-scale, feature-rich application, but rather a simple utility that does one thing well. Contributions, forks, and suggestions are welcome.
