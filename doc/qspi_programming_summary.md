# QSPI Programming Summary

Here are the exact steps I took to program only the QSPI on your Jetson Orin Nano.

1. Verified the correct QSPI-only board config  
I checked that the selected board profile was:
```bash
jetson-orin-nano-devkit-qspi
```
and confirmed it contains:
```bash
EMMC_CFG="flash_t234_qspi.xml";
NO_RECOVERY_IMG=1;
NO_ROOTFS=1;
```

2. Confirmed the device was not yet in recovery mode  
I checked the host USB view and saw:
```bash
0955:7020
```
which means the board was running normal L4T, not APX recovery mode.

3. Verified host flashing prerequisites  
I ran:
```bash
sudo /media/ranshal/jetson/L4T/nvidia_sdk/JetPack_6.2.2_Linux_JETSON_ORIN_NANO_TARGETS/Linux_for_Tegra/tools/l4t_flash_prerequisites.sh
```
This completed successfully and confirmed required packages were installed.

4. Rebooted the device into forced recovery mode  
Since the board was reachable over SSH, I used the device itself to enter recovery:
```bash
sshpass -p 'ubuntu' ssh -tt -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ubuntu@192.168.55.1 "echo ubuntu | sudo -S reboot forced-recovery"
```

5. Verified recovery mode on the host  
I checked `lsusb` again and confirmed:
```bash
0955:7523 NVIDIA Corp. APX
```
That is the correct recovery-mode USB ID for this Orin Nano target.

6. Ran the actual QSPI flash  
From the correct `Linux_for_Tegra` directory, I executed:
```bash
cd /media/ranshal/jetson/L4T/nvidia_sdk/JetPack_6.2.2_Linux_JETSON_ORIN_NANO_TARGETS/Linux_for_Tegra && sudo ./flash.sh jetson-orin-nano-devkit-qspi internal
```

7. Verified that QSPI partitions were written  
The flash log showed writes to QSPI partitions such as:
- `B_tsec-fw`
- `B_nvdec`
- `B_mb2`
- `B_cpu-bootloader`
- `B_secure-os`
- `B_eks`
- `B_dce-fw`
- `B_spe-fw`
- `B_rce-fw`
- `B_adsp-fw`
- `B_pva-fw`
- `BCT`
- `BCT-boot-chain_backup`
- `A_MB1_BCT`
- `B_MB1_BCT`
- `A_MEM_BCT`
- `B_MEM_BCT`
- `A_VER`
- `B_VER`

8. Verified successful completion  
The flash log ended with:
```text
Flashing completed
*** The target generic has been flashed successfully. ***
```

9. Verified the board booted back normally  
After the flash finished:
- `lsusb` showed `0955:7020` again
- `192.168.55.1` became reachable again

That means:
- QSPI programming succeeded
- the board cold-booted back into normal runtime Linux
