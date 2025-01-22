# Architecture

This document describes the architecture of Saphir.

## Components

The components used in Saphir are:
- PSEC Core
- GUI (provided)
- Clam Antivirus (provided) 

## Synoptic

The analysis of a disk is achieved with the following process:
- The user connects a disk to the system
- The main process is notified for the new disk and asks for the lists of files 
- The list of files are presented to the user
- The user chooses some files
- The user triggers the analysis
- The analysis process is started:
  - The files are copied to the local storage
  - The GUI asks for file analysis
  - Each antivirus analyses the file and returns the result
  - The main controller updates the GUI

## Communication mechanism

The components correspond to different virtual machines (domains). They communicate thru the PSEC messaging channel based on MQTT. In addition to PSEC grammar, there is a specific grammar for Saphir used to handle the antivirus analyses.

## Communication protocol

The messages exchanged by the components are described in this chapter.

### Commands

| Topic | Request payload | Request description | Response payload | Response description |
|--|--|--|--|--|
| `saphir/analysis` | `{ "filepath": "" }` | Triggers the analysis of a file | `{ "component": "", "filepath": "", "success": true\|false, "details": "" }` | The `component` field contains the name of the component who analyzed the file |

### Notifications

| Topic | Payload | Description | 
|--|--|--|
| `saphir/analysis/status` | `{ "filepath": "", status: "", progress: 0-100 }` | Notifies the status of analysis of a file |
