FROM python:3.8

# Copy over generated Python code and install it  
COPY leonidas/pyproject.toml /leonidas/pyproject.toml
COPY leonidas/leonidas.py /leonidas/leonidas.py
COPY leonidas/api/ /leonidas/api/
WORKDIR /leonidas
RUN pip install .

# Download and validate latest kubectl binary 
RUN curl -sLO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
 && curl -sLO "https://dl.k8s.io/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl.sha256" \
 && echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check \
 && chmod +x kubectl

ENV PATH="$PATH:/leonidas"

EXPOSE 5000

CMD ["python", "leonidas.py"]