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




const hre = require("hardhat");

async function main() {
    const [owner, user1] = await hre.ethers.getSigners();
    const walletAddress = "0x5FbDB2315678afecb367f032d93F642f64180aa3"; // Podmień na adres z deploy.js
    const Wallet = await hre.ethers.getContractFactory("SimpleWallet");
    const wallet = await Wallet.attach(walletAddress);

    console.log("Saldo przed wpłatą:", await wallet.getBalance());

    // Wysyłanie 1 ETH do kontraktu
    const tx = await wallet.connect(user1).deposit({ value: hre.ethers.utils.parseEther("1.0") });
    await tx.wait();

    console.log("Saldo po wpłacie:", await wallet.getBalance());
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
