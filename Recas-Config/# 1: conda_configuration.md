# Recas Configuration Guide

This document describes the configuration and setup procedures for the RECAS system.


## Overview

First of all, it is important to understand how the cluster works.

After obtaining the credentials to access the RECAS cluster, you must also be granted permission to submit jobs on the system (e.g. using `condor_submit`).

If you do not yet have the required permissions, please refer to the following links:

- **[Link 1](https://www.recas-bari.it/index.php/en/recas-bari-servizi-en/richiesta-credenziali-2)**: Request credentials for accessing the RECAS cluster  
- **[Link 2](https://www.recas-bari.it/index.php/en/recas-bari-servizi-en/support-request)**: Request permission to submit jobs with GPU resources (make sure to explicitly mention GPU usage in the request)

These steps are mandatory before proceeding with any job submission or configuration on the cluster.

## Overview – 2

To better understand how the cluster works, let us first introduce a simple conceptual diagram.

![RECAS cluster overview](figures/recas_cluster_overview.jpeg)

From this diagram, it is important to note that when you log into the cluster, you are **connected to the machine called the frontend**.

The frontend node has **very limited resources**, in particular:
- Limited disk space (approximately **200 MB**)
- No computational resources intended for heavy workloads

This means that the frontend **must not be used for computations**, but only for:
- Editing files
- Preparing job scripts
- Managing configurations
- Submitting jobs

This design choice is intentional: the frontend is shared by many users simultaneously. If computational workloads were allowed on the frontend, the system would quickly become overloaded and unusable for everyone.

Therefore, **any actual computation must be performed on dedicated compute nodes**.  
From the frontend, you must connect to another node of the cluster, which is a separate machine with specific computational resources (CPU, GPU, memory) allocated for your job.

In practice, the frontend acts as an **entry point and control node**, while all intensive tasks are executed on the app

## Overview – 3

![RECAS cluster overview](figures/recas_cluster_overivew_condor.jpeg)

Referring to the same diagram shown above, it is important to clarify how computations are actually executed on the cluster.

Users **cannot directly log into compute nodes**.  
Instead, access to computational resources (CPU or GPU nodes) is managed by the cluster scheduler.

On RECAS, jobs are submitted using **HTCondor**, through the command:

```bash
condor_submit file_to_submit.sub
```

## Installation - Part 1: Miniconda

Before running jobs on the RECAS cluster, it is strongly recommended to install **Miniconda**, which allows you to manage Python environments and dependencies in a clean and reproducible way.

---

### Step 0: Login to the ReCaS cluster

If you followed the guide: [0: Local machine configuration](./%23%200:%20local_machine_config.md)

you can connect to ReCaS using the alias:

```bash
ssh recas
```

Otherwise: 

```bash
ssh username@ui-al9.recas.ba.infn.it
```


### Step 1: Download and install Miniconda

Download the Miniconda installer for Linux from the official documentation:

https://docs.conda.io/projects/conda/en/stable/user-guide/install/linux.html

From the RECAS frontend, download the installer (example for 64-bit Linux):

```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
```

Make the installer executable and run it:

```bash
chmod +x Miniconda3-latest-Linux-x86_64.sh
./Miniconda3-latest-Linux-x86_64.sh
```

During the installation:
- Accept the license agreement
- Use the default installation path (recommended)
- When asked whether to initialize Miniconda, answer yes

### Step 2: Configure the .bashrc
After installation, Miniconda must be properly initialized every time you open a new shell.
Open your .bashrc file:
```bash
nano ~/.bashrc
```

Add the following lines at the end of the file:

```bash
# >>> conda initialize >>>
# !! Contents within this block are gestiti manualmente per il tuo Miniconda in home !!
__conda_setup="$('~/miniconda3/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
        . "$HOME/miniconda3/etc/profile.d/conda.sh"
    else
        export PATH="$HOME/miniconda3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<

# Attiva automaticamente l'ambiente base
conda activate base
```

Save and close the file, then reload it:

```bash
source ~/.bashrc
```

Verify that conda is available:
```bash
conda --version
```
### Step 3: Create a .bash_profile
Some login sessions use .bash_profile instead of .bashrc.
To ensure consistent behavior across all sessions, create a .bash_profile that sources .bashrc.
Create or edit the file:
```bash
nano ~/.bash_profile
```
Insert the following content:

```bash
if [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi
```
Save and close the file.


### Step 4: Ensure the base environment is always active
Log out and log back into the cluster, or open a new terminal session.
Verify that the base conda environment is active and available:
```bash
which python
conda info
```

If these commands work correctly, Miniconda is properly installed and configured.

## Final Notes
Miniconda is installed locally in your home directory and does not require administrator privileges.
Do not install the full Anaconda distribution (too heavy for cluster usage).
Always use conda environments for project-specific software and experiments.
Never run computational workloads directly on the frontend.


## Installation – Part 2: Creating the Conda Environment

As stated previously, before creating and using a conda environment, you must run commands on a **compute node**, not on the frontend.

The frontend **must never be used for installations or heavy operations**.  
It is only used to:
- prepare files
- submit jobs
- manage configurations

To actually work on a compute node, we use **HTCondor in interactive mode**.

### Where This Is Done

All the following steps are performed **from the frontend**:

- the submission file (`backend.sub`) is created **on the frontend**
- the job is submitted **from the frontend**
- HTCondor will then assign you a **compute node**

---

### Accessing a Compute Node (Interactive Job)

To access a compute node, you must submit an **interactive HTCondor job**.

This gives you a temporary shell on a compute node with the resources you request, and keeps the session open while you work.

### Let's start: 'backend.sub'"

Create a file called `backend.sub` **on the frontend**  
(or download it from the repository: `files/backend.sub`).

```bash
output = out
error  = err
log    = log

request_cpus   = 1
request_gpus   = 0
request_memory = 2048

getenv = true

rank = Memory
queue
```

#### Meaning of the Requested Resources
- **`request_cpus = 1`**  
  Requests a single CPU core for job execution.

- **`request_gpus = 0`**  
  Indicates that no GPU resources are required; the job will run on a CPU-only node.

- **`request_memory = 2048`**  
  Requests 2 GB of RAM to be allocated to the job.

- **`getenv = true`**  
  Inherits the environment variables from the submission environment.

- **`rank = Memory`**  
  Instructs the scheduler to prioritize execution on nodes with higher available memory.

You can change the parameters as you wish. 

#### Why this submission file is needed
This submission file is used to allocate computational resources and establish an interactive session on a compute node.
If the job is submitted without an interactive command, it will immediately terminate, because no executable or persistent task is defined—only resource requests are made.

By using an interactive job, you gain direct access to the allocated node and can work on it continuously until the session is explicitly closed.
In other words, the interactive mode keeps the job alive, allowing you to:
- Use the allocated CPU and memory interactively
- Run commands manually on the compute node
- Maintain control of the session for as long as needed

###
Submitting an Interactive Job
Submit the job in interactive mode using:

```bash
condor_submit -interactive backend.sub
```

Once the job starts, you will be connected directly to a compute node with the requested resources.
This interactive session remains open, allowing you to:

- **`install softwares`**
- **`create conda environments`**  
- **`test commands`**
- **`prepare scripts for batch execution`**

This is what it will look like if everything worked fine:
 
![RECAS cluster overview](figures/welcome_to_a_node.png)


###

At this point you are inside the cluster. Here, if everything is correctly configured, you can create your own env, with 


```bash
conda create YOUR_ENV_NAME python==YOUR_PYTHON_VERSION
```
and proceed creating your own env with the requirements you need.

#### Important Notes on Interactive Jobs
The more resources you request, the longer the waiting time may be.
Always request the minimum resources needed.
Interactive jobs are meant for setup and testing, not long computations.
When the session ends, the node is released automatically.


