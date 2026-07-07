# C++ -> WASM compile service for in-browser milestones.
# emsdk ships emcc + python3; Eigen is added for the Phase V exercise.
FROM emscripten/emsdk:3.1.61

ADD https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.tar.gz /tmp/eigen.tar.gz
RUN mkdir -p /opt/eigen && \
    tar -xzf /tmp/eigen.tar.gz -C /opt/eigen --strip-components=1 && \
    rm /tmp/eigen.tar.gz

COPY server.py /srv/server.py

# Prewarm emscripten's system-library cache so first user compile is fast.
RUN printf '#include <cstdio>\nint main(){puts("warm");}\n' > /tmp/warm.cpp && \
    emcc /tmp/warm.cpp -o /tmp/warm.mjs -std=c++20 -O1 \
      -sMODULARIZE=1 -sEXPORT_ES6=1 -sSINGLE_FILE=1 -sEXIT_RUNTIME=1 \
      -sENVIRONMENT=web,worker,node && \
    rm /tmp/warm.cpp /tmp/warm.mjs

EXPOSE 8080
CMD ["python3", "/srv/server.py"]
