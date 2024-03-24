FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y ffmpeg git python3 python3-pip curl python3-venv && apt-get autoremove -y && apt-get clean
WORKDIR /root
RUN git clone https://github.com/aarnphm/whispercpp
WORKDIR /root/whispercpp
RUN ./tools/bazel build //:whispercpp_wheel --repo_env PYTHON_BIN_PATH='/usr/bin/python3' &&  pip install $(./tools/bazel info bazel-bin)/*.whl && rm -rf ../whispercpp
WORKDIR /root
RUN git clone https://github.com/sergarb1/telegram-bot-whisper-cpp
WORKDIR /root/telegram-bot-whisper-cpp
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python3","/root/telegram-bot-whisper-cpp/main.py"]
