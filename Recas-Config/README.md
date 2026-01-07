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

![RECAS cluster overview](figures/recas_cluster_overview.png)

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

![RECAS cluster overview](figures/recas_cluster_overview_condor.png)

Referring to the same diagram shown above, it is important to clarify how computations are actually executed on the cluster.

Users **cannot directly log into compute nodes**.  
Instead, access to computational resources (CPU or GPU nodes) is managed by the cluster scheduler.

On RECAS, jobs are submitted using **HTCondor**, through the command:

```bash
condor_submit file_to_submit.sub


## Installation

