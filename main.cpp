#include <iostream>

#include <string>

#define TAX_RATE 0.15;

using namespace std;

int main()
{
	cout<<"This program takes inputs from the user and then calculates the products and sales of the inventory"<<endl;
	cout<<"C++ is a compiled language means that it should be fully converted to machine code before execution"<<endl;
	string productName;
	int productCategory;
	int initialQuantity;
	float productPrice;
	int itemsSold;
	const double taxRate = 0.15;
	cout<<"Enter the product name (single word): ";
	cin>>productName;
	cout<<"Enter the product category (integer from 1 to 5): ";
	cin>>productCategory;
	cout<<"Enter the initial inventory quantity: ";
	cin>>initialQuantity;
	cout<<"Enter the product price: ";
	cin>>productPrice;
	cout<<"Enter amount of items sold: ";
	cin>>itemsSold;
	int newInventory = initialQuantity-itemsSold;
	float totalSales;
	totalSales = itemsSold*productPrice; //example of assignment after declaration
	string inventoryStatus;
	if(newInventory<10) inventoryStatus = "Low inventory";
	else inventoryStatus = "sufficient inventory";
	auto totalSalesDemo = totalSales; //example of direct initialization
    decltype(initialQuantity) inventoryDemo = newInventory;
    cout<<"The product name is: "<<productName<<endl;
    cout<<"The product category is: "<<productCategory<<endl;
    cout<<"The initial inventory quantity is: "<<initialQuantity<<endl;
    cout<<"The product price is: "<<productPrice<<endl;
    cout<<"The total items sold is: "<<itemsSold<<endl;
	cout<<"The total revenue you generated is: "<<totalSales<<endl;
	int listIntialization {123}; //example of list initialization

}
