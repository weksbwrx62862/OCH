# ClawPanel OpenClaw Detection Plan

## [x] Task 1: Check OpenClaw CLI installation
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - Verify that OpenClaw CLI is installed and accessible
- **Success Criteria**:
  - OpenClaw CLI is installed and can be run from the command line
- **Test Requirements**:
  - `programmatic` TR-1.1: `openclaw --version` returns the version number
- **Notes**: Checks if OpenClaw CLI is properly installed and in the PATH

## [x] Task 2: Check OpenClaw configuration directory
- **Priority**: P0
- **Depends On**: Task 1
- **Description**:
  - Verify the location of the OpenClaw configuration directory
- **Success Criteria**:
  - The configuration directory exists and contains the necessary files
- **Test Requirements**:
  - `programmatic` TR-2.1: `ls -la /home/xxh/.openclaw` shows the configuration files
- **Notes**: ClawPanel seems to be looking at /home/xxh/openclaw, but the actual directory might be /home/xxh/.openclaw

## [/] Task 3: Check ClawPanel configuration
- **Priority**: P0
- **Depends On**: Task 2
- **Description**:
  - Check how ClawPanel is configured to find OpenClaw
- **Success Criteria**:
  - Understand how ClawPanel determines the OpenClaw CLI location and configuration directory
- **Test Requirements**:
  - `programmatic` TR-3.1: Check the ClawPanel source code or configuration files for OpenClaw detection logic
- **Notes**: This will help us understand why ClawPanel is not detecting OpenClaw

## [ ] Task 4: Fix OpenClaw detection
- **Priority**: P0
- **Depends On**: Task 3
- **Description**:
  - Fix the issue where ClawPanel is not detecting OpenClaw
- **Success Criteria**:
  - ClawPanel successfully detects the OpenClaw CLI and configuration directory
- **Test Requirements**:
  - `human-judgement` TR-4.1: ClawPanel shows OpenClaw CLI as installed
- **Notes**: This might involve updating ClawPanel's configuration or creating a symlink

## [ ] Task 5: Verify the fix
- **Priority**: P0
- **Depends On**: Task 4
- **Description**:
  - Verify that ClawPanel now correctly detects OpenClaw
- **Success Criteria**:
  - ClawPanel shows all checks as passed
- **Test Requirements**:
  - `human-judgement` TR-5.1: ClawPanel shows OpenClaw CLI as installed and configuration file found
- **Notes**: Final verification step to ensure the fix works