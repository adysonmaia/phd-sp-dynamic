# Dynamic Service Placement

## Installation
1. Install Python 3.6 or superior 
2. Create virtual environment
    ```sh   
    python3 -m venv ./venv --system-site-packages
    ```
3. Activate virtual environment
    ```sh   
    source ./venv/bin/activate
    ```
4. Install required packages
    ```sh
    pip3 install -r requirements.txt
    ```
5. Install service placement module in development mode
    ```sh
    pip3 install -e .
    ``` 

## Documentation
1. Generate documentation
    ```sh
    chmod a+x gen_doc.sh
    ./gen_doc.sh
    ```
2. Open documentation
    ```sh
    open ./docs/build/html/index.html
    ```