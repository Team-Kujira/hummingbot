# Docker

## Hummingbot Installation Guide
 - https://www.youtube.com/watch?v=t3Su_F_SY_0
 - https://docs.hummingbot.org/installation/
 - https://docs.hummingbot.org/quickstart/

## Client

### Creation

Run:

> ./client/create-client.sh

to create a Client instance. Follow the instructions on the screen.

Important: it is needed to be located at the scripts folders, seeing the client folder, otherwise the Dockerfile
will not be able to copy the required files.

### Configuration

#### Generate Certificates
From the Hummingbot command line type:

> gateway generate-certs

for creating the certificates. Take note about the passphrase used, it is needed for configuring the Gateway.

## Gateway

### Creation

Run:

> ./gateway/create-gateway.sh

to create a Gateway instance. Follow the instructions on the screen
and enter the same passphrase created when configuring the Client.

Important: it is needed to be located in the scripts folders, seeing the gateway folder, otherwise the Dockerfile
will not be able to copy the required files.

### Configuration

The Gateway will only start properly if the `./shared/common/certs` contains the certificates
and the informed passphrase is the correct one.

## Running

All of the commands given here are for the Hummingbot Client command line.

### Connecting the Wallet
Connect to the Kujira wallet with:

> gateway connect kujira

follow the instructions on the screen.

After the wallet configuration check if it is working with:

> balance

You should see the balances of each token you have in your wallet.

Important: before running the script, check if you have a minimal balance in the two tokens
for the target market. For example, if the market is DEMO-USK, it is needed to have a minimal
amount in DEMO and USK tokens. Also, it is needed to have a minimum amount of KUJI tokens
to pay the transaction fees.

### Running a PMM Script

Check if the

> ./shared/client/scripts/kujira_pmm_example.py

file has the appropriate configurations.

After that you can start the script as the following:

> start --script kujira_pmm_script_example.py

After that the PMM script will start to run.

It is possible to check the logs on the right side of the Client screen or by the command line with:

> tail -f shared/client/logs/* shared/gateway/logs/*

## Running a PMM Strategy

Check if the

> ./shared/client/strategies/kujira_pmm_strategy_example.yml

file has the appropriate configurations.

Import the strategy with:

> import kujira_pmm_strategy_example

And start the strategy with:

> start

Hummingbot might ask if you want to start the strategy, type "Yes".

After that the PMM strategy will start to run.

It is possible to check the logs on the right side of the Client screen or by the command line with:

> tail -f shared/client/logs/* shared/gateway/logs/*
> 