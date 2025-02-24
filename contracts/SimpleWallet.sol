// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract SimpleWallet {
    address public owner;

    // Wydarzenia logujące wpłaty i wypłaty
    event Deposited(address indexed sender, uint amount);
    event Withdrawn(address indexed receiver, uint amount);

    constructor() {
        owner = msg.sender;  // Osoba, która wdroży kontrakt, zostaje właścicielem
    }

    // Funkcja do wpłacania ETH do kontraktu
    function deposit() public payable {
        require(msg.value > 0, "Musisz wyslac jakas wartosc!");
        emit Deposited(msg.sender, msg.value);
    }

    // Funkcja do sprawdzenia salda kontraktu
    function getBalance() public view returns (uint) {
        return address(this).balance;
    }

    // Funkcja do wypłacania ETH - tylko właściciel może to zrobić
    function withdraw(uint _amount) public {
        require(msg.sender == owner, "Tylko wlasciciel moze wyplacac!");
        require(address(this).balance >= _amount, "Brak wystarczajacych srodkow!");
        
        payable(owner).transfer(_amount);
        emit Withdrawn(owner, _amount);
    }
}