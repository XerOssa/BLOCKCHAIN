const hre = require("hardhat");

async function main() {
  // Pobierz fabrykę kontraktu
  const Wallet = await hre.ethers.getContractFactory("SimpleWallet");

  // Wdróż kontrakt
  const wallet = await Wallet.deploy(); // ✅ Teraz poprawnie wdrażamy kontrakt

  await wallet.waitForDeployment(); // ✅ Poczekaj, aż się wdroży

  console.log("Contract deployed to:", await wallet.getAddress());
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});



