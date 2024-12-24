# !/bin/bash
echo "Packaging the Lambda Function with all depencdencies"

export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1
cd /home/
python -m venv env
source ./env/bin/activate
pip install --no-cache-dir requests google-generativeai pillow

mkdir /home/python/
cp -r /home/env/lib /home/python/
apk add zip
cd /home/python
zip -r python.zip .
mv python.zip /home/app/


mkdir /home/code
cd /home/code/
cp -r /home/app/images /home/code/
cp /home/app/lambda_function.py /home/code/
zip -r gemini.zip .
mv gemini.zip /home/app/
echo "Lambda Function is packaged Successfully"

python /home/app/lambda_function.py && echo "Ready to GO"
deactivate