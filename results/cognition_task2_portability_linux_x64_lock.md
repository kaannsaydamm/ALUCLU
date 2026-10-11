# Task 2.7 Linux x86_64 portability dependency snapshot

Clean clone commit: `866c6d075cd64e4f956011703964e988ec26bdc7`.
Guest: Kali GNU/Linux 2026.1 under WSL2, kernel `6.18.33.2-microsoft-standard-WSL2`, x86_64, glibc 2.42.
Each lane used its own isolated venv and `python -m pip install -e ".[test]"` from the exact clone before the 215-test selected suite. The editable VCS entry in `pip freeze` identifies that source commit; future clean clones should install their own checkout at the same commit.
This is an observed environment snapshot, not a cross-platform lock or a portability claim for macOS/arm64.

## CPython 3.10.21

```text
-e git+https://github.com/kaannsaydamm/ALUCLU.git@866c6d075cd64e4f956011703964e988ec26bdc7#egg=aluclu_memory
cffi==2.1.1
cryptography==50.0.1
cuda-bindings==13.4.2
cuda-pathfinder==1.8.2
cuda-toolkit==13.0.3.0
exceptiongroup==1.3.1
filelock==4.0.0
fsspec==2026.7.0
iniconfig==2.3.0
Jinja2==3.1.6
MarkupSafe==3.0.3
mpmath==1.3.0
networkx==3.4.2
numpy==2.2.6
nvidia-cublas==13.1.1.3
nvidia-cuda-cupti==13.0.85
nvidia-cuda-nvrtc==13.0.88
nvidia-cuda-runtime==13.0.96
nvidia-cudnn-cu13==9.24.0.43
nvidia-cufft==12.0.0.61
nvidia-cufile==1.15.1.6
nvidia-curand==10.4.0.35
nvidia-cusolver==12.0.4.66
nvidia-cusparse==12.6.3.3
nvidia-cusparselt-cu13==0.8.1
nvidia-nccl-cu13==2.30.7
nvidia-nvjitlink==13.4.92
nvidia-nvshmem-cu13==3.4.5
nvidia-nvtx==13.0.85
packaging==26.3
pluggy==1.6.0
pycparser==3.0
Pygments==2.21.0
pytest==9.1.1
sympy==1.14.0
tomli==2.4.1
torch==2.14.0
triton==3.8.0
typing_extensions==4.16.0
```

## CPython 3.11.16

```text
-e git+https://github.com/kaannsaydamm/ALUCLU.git@866c6d075cd64e4f956011703964e988ec26bdc7#egg=aluclu_memory
cffi==2.1.1
cryptography==50.0.1
cuda-bindings==13.4.2
cuda-pathfinder==1.8.2
cuda-toolkit==13.0.3.0
filelock==4.0.0
fsspec==2026.7.0
iniconfig==2.3.0
Jinja2==3.1.6
MarkupSafe==3.0.3
mpmath==1.3.0
networkx==3.6.1
numpy==2.4.6
nvidia-cublas==13.1.1.3
nvidia-cuda-cupti==13.0.85
nvidia-cuda-nvrtc==13.0.88
nvidia-cuda-runtime==13.0.96
nvidia-cudnn-cu13==9.24.0.43
nvidia-cufft==12.0.0.61
nvidia-cufile==1.15.1.6
nvidia-curand==10.4.0.35
nvidia-cusolver==12.0.4.66
nvidia-cusparse==12.6.3.3
nvidia-cusparselt-cu13==0.8.1
nvidia-nccl-cu13==2.30.7
nvidia-nvjitlink==13.4.92
nvidia-nvshmem-cu13==3.4.5
nvidia-nvtx==13.0.85
packaging==26.3
pluggy==1.6.0
pycparser==3.0
Pygments==2.21.0
pytest==9.1.1
sympy==1.14.0
torch==2.14.0
triton==3.8.0
typing_extensions==4.16.0
```

## CPython 3.12.14

```text
-e git+https://github.com/kaannsaydamm/ALUCLU.git@866c6d075cd64e4f956011703964e988ec26bdc7#egg=aluclu_memory
cffi==2.1.1
cryptography==50.0.1
cuda-bindings==13.4.2
cuda-pathfinder==1.8.2
cuda-toolkit==13.0.3.0
filelock==4.0.0
fsspec==2026.9.0
iniconfig==2.3.0
Jinja2==3.1.6
MarkupSafe==3.0.3
mpmath==1.3.0
networkx==3.6.1
numpy==2.5.3
nvidia-cublas==13.1.1.3
nvidia-cuda-cupti==13.0.85
nvidia-cuda-nvrtc==13.0.88
nvidia-cuda-runtime==13.0.96
nvidia-cudnn-cu13==9.24.0.43
nvidia-cufft==12.0.0.61
nvidia-cufile==1.15.1.6
nvidia-curand==10.4.0.35
nvidia-cusolver==12.0.4.66
nvidia-cusparse==12.6.3.3
nvidia-cusparselt-cu13==0.8.1
nvidia-nccl-cu13==2.30.7
nvidia-nvjitlink==13.4.92
nvidia-nvshmem-cu13==3.4.5
nvidia-nvtx==13.0.85
packaging==26.3
pluggy==1.6.0
pycparser==3.0
Pygments==2.21.0
pytest==9.1.1
setuptools==84.0.0
sympy==1.14.0
torch==2.14.0
triton==3.8.0
typing_extensions==4.16.0
```

## CPython 3.13.12

```text
-e git+https://github.com/kaannsaydamm/ALUCLU.git@866c6d075cd64e4f956011703964e988ec26bdc7#egg=aluclu_memory
cffi==2.1.1
cryptography==50.0.1
cuda-bindings==13.4.2
cuda-pathfinder==1.8.2
cuda-toolkit==13.0.3.0
filelock==4.0.0
fsspec==2026.7.0
iniconfig==2.3.0
Jinja2==3.1.6
MarkupSafe==3.0.3
mpmath==1.3.0
networkx==3.6.1
numpy==2.5.3
nvidia-cublas==13.1.1.3
nvidia-cuda-cupti==13.0.85
nvidia-cuda-nvrtc==13.0.88
nvidia-cuda-runtime==13.0.96
nvidia-cudnn-cu13==9.24.0.43
nvidia-cufft==12.0.0.61
nvidia-cufile==1.15.1.6
nvidia-curand==10.4.0.35
nvidia-cusolver==12.0.4.66
nvidia-cusparse==12.6.3.3
nvidia-cusparselt-cu13==0.8.1
nvidia-nccl-cu13==2.30.7
nvidia-nvjitlink==13.4.92
nvidia-nvshmem-cu13==3.4.5
nvidia-nvtx==13.0.85
packaging==26.3
pluggy==1.6.0
pycparser==3.0
Pygments==2.21.0
pytest==9.1.1
setuptools==84.0.0
sympy==1.14.0
torch==2.14.0
triton==3.8.0
typing_extensions==4.16.0
uv==0.12.16
```
