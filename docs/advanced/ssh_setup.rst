SSH Setup for Remote Machines
==============================

To use TomoGUI's batch processing on remote machines (tomo1-5), you need to configure passwordless SSH authentication.

Prerequisites
-------------

Before configuring SSH:

- Remote machines must be accessible on your network
- You need a user account on each remote machine
- TomoCuPy must be installed on remote machines
- Data files must be accessible (via NFS/shared storage)

SSH Key Generation
------------------

Generate SSH Keys
~~~~~~~~~~~~~~~~~

If you don't already have SSH keys:

.. code-block:: bash

   ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

Follow the prompts:

.. code-block:: text

   Enter file in which to save the key: [Press Enter for default]
   Enter passphrase (empty for no passphrase): [Press Enter]
   Enter same passphrase again: [Press Enter]

**Note**: Use an empty passphrase for passwordless authentication.

Your keys are now in:
   - Private key: ``~/.ssh/id_rsa``
   - Public key: ``~/.ssh/id_rsa.pub``

Copy Public Key to Remote Machines
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For each remote machine, copy your public key:

.. code-block:: bash

   ssh-copy-id username@tomo1
   ssh-copy-id username@tomo2
   ssh-copy-id username@tomo3
   ssh-copy-id username@tomo4
   ssh-copy-id username@tomo5

You'll be prompted for your password on the remote machine. After this, passwordless login should work.

Manual Key Installation
~~~~~~~~~~~~~~~~~~~~~~~

If ``ssh-copy-id`` is not available:

.. code-block:: bash

   # Display your public key
   cat ~/.ssh/id_rsa.pub

   # SSH to remote machine
   ssh username@tomo1

   # On remote machine, add key to authorized_keys
   mkdir -p ~/.ssh
   chmod 700 ~/.ssh
   echo "PASTE_YOUR_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   exit

Repeat for each remote machine.

Verifying SSH Setup
--------------------

Test Passwordless Login
~~~~~~~~~~~~~~~~~~~~~~~

Test each remote machine:

.. code-block:: bash

   ssh tomo1
   # Should connect without asking for password
   exit

   ssh tomo2
   exit

   # Test all machines
   for i in {1..5}; do
       echo "Testing tomo$i..."
       ssh tomo$i "hostname"
   done

Expected output:

.. code-block:: text

   Testing tomo1...
   tomo1
   Testing tomo2...
   tomo2
   ...

If prompted for password, SSH key setup failed.

Test Command Execution
~~~~~~~~~~~~~~~~~~~~~~

Verify you can run commands remotely:

.. code-block:: bash

   ssh tomo1 "which tomocupy"
   # Should output: /path/to/tomocupy

   ssh tomo1 "nvidia-smi --query-gpu=name --format=csv,noheader"
   # Should list GPU names

SSH Configuration
-----------------

Create SSH Config File
~~~~~~~~~~~~~~~~~~~~~~

For easier access, create ``~/.ssh/config``:

.. code-block:: text

   # Tomo reconstruction machines
   Host tomo1
       HostName tomo1.facility.domain
       User your_username
       IdentityFile ~/.ssh/id_rsa
       ServerAliveInterval 60
       ServerAliveCountMax 3

   Host tomo2
       HostName tomo2.facility.domain
       User your_username
       IdentityFile ~/.ssh/id_rsa
       ServerAliveInterval 60
       ServerAliveCountMax 3

   Host tomo3
       HostName tomo3.facility.domain
       User your_username
       IdentityFile ~/.ssh/id_rsa
       ServerAliveInterval 60
       ServerAliveCountMax 3

   Host tomo4
       HostName tomo4.facility.domain
       User your_username
       IdentityFile ~/.ssh/id_rsa
       ServerAliveInterval 60
       ServerAliveCountMax 3

   Host tomo5
       HostName tomo5.facility.domain
       User your_username
       IdentityFile ~/.ssh/id_rsa
       ServerAliveInterval 60
       ServerAliveCountMax 3

Adjust:
   - ``HostName``: Full hostname or IP address
   - ``User``: Your username on remote machines
   - ``IdentityFile``: Path to your private key

Configuration Options
~~~~~~~~~~~~~~~~~~~~~

Useful SSH config options:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Option
     - Purpose
   * - ServerAliveInterval 60
     - Send keepalive every 60 seconds
   * - ServerAliveCountMax 3
     - Disconnect after 3 failed keepalives
   * - ConnectTimeout 10
     - Timeout connection after 10 seconds
   * - StrictHostKeyChecking no
     - Don't prompt for host verification (use with caution)
   * - UserKnownHostsFile /dev/null
     - Don't save host keys (use with caution)

Shared Storage Setup
--------------------

NFS Mount Configuration
~~~~~~~~~~~~~~~~~~~~~~~

Remote machines must access the same data files. Common solutions:

**NFS (Network File System)**:

On data server:

.. code-block:: bash

   # Export directory (add to /etc/exports)
   /data/tomography 192.168.1.0/24(rw,sync,no_subtree_check)

   # Restart NFS
   sudo exportfs -ra

On remote machines:

.. code-block:: bash

   # Mount NFS share
   sudo mount -t nfs data-server:/data/tomography /data/tomography

   # Add to /etc/fstab for automatic mounting
   data-server:/data/tomography /data/tomography nfs defaults 0 0

Verifying File Access
~~~~~~~~~~~~~~~~~~~~~

Ensure all machines see the same files:

.. code-block:: bash

   # On local machine
   ls /data/tomography/scan_001/

   # On remote machines
   ssh tomo1 "ls /data/tomography/scan_001/"
   ssh tomo2 "ls /data/tomography/scan_001/"

Paths must match exactly.

Environment Setup
-----------------

Remote Environment Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

TomoCuPy needs proper environment setup on remote machines.

Add to remote ``~/.bashrc`` or ``~/.bash_profile``:

.. code-block:: bash

   # CUDA
   export PATH=/usr/local/cuda/bin:$PATH
   export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH

   # TomoCuPy
   export PATH=/opt/tomocupy/bin:$PATH

   # Python environment
   source /opt/conda/bin/activate tomocupy

Test environment:

.. code-block:: bash

   ssh tomo1 "which tomocupy && tomocupy --version"

GPU Access
~~~~~~~~~~

Verify GPU access on remote machines:

.. code-block:: bash

   ssh tomo1 "nvidia-smi"

Should show GPU information without errors.

Troubleshooting SSH Issues
---------------------------

Permission Denied
~~~~~~~~~~~~~~~~~

If you get "Permission denied":

.. code-block:: bash

   # Check SSH key permissions
   chmod 600 ~/.ssh/id_rsa
   chmod 644 ~/.ssh/id_rsa.pub
   chmod 700 ~/.ssh

   # On remote machine
   ssh tomo1
   chmod 700 ~/.ssh
   chmod 600 ~/.ssh/authorized_keys

Connection Refused
~~~~~~~~~~~~~~~~~~

If connection is refused:

.. code-block:: bash

   # Check if SSH daemon is running on remote machine
   ssh tomo1 "systemctl status sshd"

   # Check firewall rules
   ssh tomo1 "sudo iptables -L | grep ssh"

   # Verify SSH is listening on port 22
   ssh tomo1 "netstat -tlnp | grep :22"

Host Key Verification Failed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If host key changes:

.. code-block:: bash

   # Remove old host key
   ssh-keygen -R tomo1

   # Reconnect (will prompt to add new key)
   ssh tomo1

Timeout Issues
~~~~~~~~~~~~~~

For slow or unreliable connections:

Add to ``~/.ssh/config``:

.. code-block:: text

   Host tomo*
       ConnectTimeout 30
       ServerAliveInterval 30
       ServerAliveCountMax 5
       TCPKeepAlive yes

Command Not Found on Remote
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If tomocupy is not found:

.. code-block:: bash

   # Use full path in TomoGUI, or
   # Add to remote ~/.bashrc:
   export PATH=/path/to/tomocupy:$PATH

   # Source bashrc for non-interactive shells
   # Add to ~/.bash_profile or ~/.bashrc:
   if [ -f ~/.bashrc ]; then
       source ~/.bashrc
   fi

Security Considerations
-----------------------

Best Practices
~~~~~~~~~~~~~~

1. **Use SSH keys** instead of passwords
2. **Protect private keys**: ``chmod 600 ~/.ssh/id_rsa``
3. **Use passphrases** for keys in sensitive environments
4. **Limit key access**: Only copy to trusted machines
5. **Regular key rotation**: Generate new keys periodically
6. **Monitor access**: Check ``~/.ssh/authorized_keys`` regularly

SSH Agent
~~~~~~~~~

For passphrase-protected keys:

.. code-block:: bash

   # Start SSH agent
   eval "$(ssh-agent -s)"

   # Add key to agent
   ssh-add ~/.ssh/id_rsa

   # Verify keys loaded
   ssh-add -l

Now you can use passphrase-protected keys without entering the passphrase each time.

Firewall Rules
~~~~~~~~~~~~~~

Ensure SSH port (22) is open:

.. code-block:: bash

   # On remote machine
   sudo ufw allow 22/tcp
   sudo ufw enable

Advanced Configuration
----------------------

SSH Multiplexing
~~~~~~~~~~~~~~~~

For faster repeated connections, use multiplexing:

Add to ``~/.ssh/config``:

.. code-block:: text

   Host tomo*
       ControlMaster auto
       ControlPath ~/.ssh/control-%r@%h:%p
       ControlPersist 10m

This reuses existing connections for 10 minutes.

Jump Hosts
~~~~~~~~~~

If remote machines are behind a gateway:

.. code-block:: text

   Host gateway
       HostName gateway.facility.domain
       User username

   Host tomo*
       ProxyJump gateway

Now ``ssh tomo1`` automatically jumps through the gateway.

Testing from TomoGUI
--------------------

Verify Setup in TomoGUI
~~~~~~~~~~~~~~~~~~~~~~~

1. Launch TomoGUI
2. Navigate to Batch Processing tab
3. Set Target Machine to "tomo1"
4. Select one file
5. Click "Run Try on Selected"
6. Check log output for:

   .. code-block:: text

      🖥️ Running on tomo1: scan_001.h5
      🚀 Started try on GPU 0: scan_001.h5

If you see errors, check:
   - SSH configuration
   - Remote machine accessibility
   - TomoCuPy installation
   - File path access

Getting Help
------------

If SSH setup fails after following this guide:

1. Check error messages carefully
2. Verify each step was completed
3. Test SSH manually before using TomoGUI
4. Check remote machine logs: ``/var/log/auth.log``
5. Contact your system administrator
6. Consult SSH documentation: ``man ssh`` or ``man ssh_config``
