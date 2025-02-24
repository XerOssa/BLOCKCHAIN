const hre = require("hardhat");

async function main() {
  const walletAddress = "0x5FbDB2315678afecb367f032d93F642f64180aa3";
  const Wallet = await hre.ethers.getContractFactory("SimpleWallet");
  const wallet = await Wallet.attach(walletAddress);

  const balance = await wallet.getBalance(); // jeśli masz taką funkcję
  console.log("Wallet balance:", balance.toString());
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
