# 0: local_machine_config.md

## Configure SSH access to ReCaS

To simplify the SSH connection to **ReCaS**, you can configure your local SSH client by editing the SSH config file on your machine.

### Step 1: Open the SSH config file

On your **local machine**, open (or create, if it does not exist) the SSH configuration file:

```bash
nano ~/.ssh/config
```

Step 2: Add the ReCaS configuration

Copy and paste the following block into the file:
```bash
Host recas
  HostName ui-al9.recas.ba.infn.it
  User YOUR_USERNAME
```
Replace **YOUR_USERNAME with your personal ReCaS username**.

Once configured, you can connect to ReCaS simply by running:
```bash
ssh recas
```

This avoids typing the full hostname and username every time and ensures a cleaner, more reliable SSH workflow.
