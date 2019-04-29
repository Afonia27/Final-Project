/*
Created by Afanasi Chihaioglo on 03/02/19
This program is capable of measuring voltage, current, temperature using related sensor
Screen is used to create the HMI 
The different tests can be peformed by changing the TestRoutine 
It also connects to the motor controller using PWM
 */

#include <LFlash.h>
#include <LSD.h>
#include <LStorage.h>
#include <Servo.h>
#include <Wire.h> // Used to establied serial communication on the I2C bus
#include "SparkFunTMP102.h" // Used to send and recieve specific information from our sensor
#define Drv LFlash          // use Internal 10M Flash
//#define Drv LSD           // use SD card

#include <LiquidCrystal_I2C.h> // Screen Setups
LiquidCrystal_I2C lcd(0x27,20,4);
TMP102 sensor0(0x48); // Initialize sensor at I2C address 0x48
Servo myservo;


String CurrentName[10] = {"current1.csv","current2.csv","current3.csv","current4.csv","current5.csv","current6.csv","current7.csv","current8.csv","current9.csv","current10.csv"};
String VoltageName[10] = {"voltage1.csv","voltage2.csv","voltage3.csv","voltage4.csv","voltage5.csv","voltage6.csv","voltage7.csv","voltage8.csv","voltage9.csv","voltage10.csv"};
int name_count = 0;
boolean foo = 0; 
float temperature = 0.0;
uint32_t InterruptPinD2 = 0;
int screen = 1;
boolean measurement_flag = 0; 
int routine_time = 10000; // 10 sec

float sum = 0.0;
char filechar[20];

//---------------------------Voltage Sensor---------------------------
float VoltageValues[300];
float voltage = 0.0;
float vout = 0.0;
float vin = 0.0;
float R1 = 96000.0; // resistance of R1 (100K) -see text!
float R2 = 9970.0; //10000.0; // resistance of R2 (10K) - see text!
int value = 0;
float offset = 1.2;  // 7.45/6.23 


//---------------------------Current Sensor---------------------------
float CurrentValues[300];
float current = 0.0;

float hall_voltage = 0.0;
const int analogInPin = A0;

// Number of samples to average the reading over
// Change this to make the reading smoother... but beware of buffer overflows!
const int avgSamples = 7;

int sensorValue = 0;

float sensitivity = 0.503; //0.39; //66; //8122.4;//100.0 / 500.0; //100mA per 500mV = 0.2
float Vref = 2465; // Output voltage with no current: ~ 2500mV or 2.5V
//-------------------------------------------

void setup()
{

    lcd.init(); // Activate the LCD screen 
    lcd.backlight(); 
    lcd.print("Hello");
    delay(1000);
    lcd.clear();
    // Open serial communications and wait for port to open:
    //Serial.begin(9600);
    Serial.begin(115200);
    myservo.attach(9);
    pinMode(2,INPUT_PULLUP);
    //digitalWrite(2,HIGH);
    pinMode(3,INPUT_PULLUP);
    attachInterrupt(1,ISR,FALLING); // 1 Corresponds to pin 3 (D3)
    interrupts();
    //Serial.print("Initializing SD card...");
    //lcd.print("Initializing SD card...");
    // make sure that the default chip select pin is set to
    // output, even if you don't use it:
    pinMode(10, OUTPUT);
    delay(1000);
    // see if the card is present and can be initialized:
    Drv.begin();
    //Serial.println("card initialized.");
    //lcd.println("card initialized.");
    
    sensor0.begin(); // initialise the temp sensor
    // set the Conversion Rate (how quickly the sensor gets a new reading)
    //0-3: 0:0.25Hz, 1:1Hz, 2:4Hz, 3:8Hz
    sensor0.setConversionRate(2);
    //set Extended Mode.
    //0:12-bit Temperature(-55C to +128C) 1:13-bit Temperature(-55C to +150C)
    sensor0.setExtendedMode(0);


}

void loop()
{
  // make a string for assembling the data to log:


  switch(screen)
  {
    case 1:
    {
      lcd.clear();
      //Serial.println("Availiable");
      if (CheckVoltage() == 0)
      {
      lcd.print("Press button to");
      lcd.setCursor(0,1);
      lcd.print("Start ");
      lcd.print(CheckTemp());
      delay(500);
      }
      else if (CheckVoltage() == 1)
      {
      lcd.print("Press button to");
      lcd.setCursor(0,1);
      lcd.print("Start");
      lcd.setCursor(0,2);
      lcd.print("Bat Detected");
      delay(500);
      }
      if (measurement_flag == 1)
      {
        TestRoutine2();
        measurement_flag = 0;
      }
    }
  }


  
}

boolean CheckVoltage()
{
  boolean VoltageFlag;
  voltage = analogRead(A1);
  vout = (voltage * 5.0) / 1024.0; // see text
  vin = vout / (R2/(R1+R2));
  vin = vin * offset; 
  if (vin<0.09) 
  {
  vin=0.0;//statement to quash undesired reading !
  }
  if (vin > 1.5)
  {
    VoltageFlag = 1;
  }
  else if (vin < 1.5)
  {
    VoltageFlag = 0;
  }

  return VoltageFlag;
}

float CheckCurrent()
{
  current = 0.0;
  for (int i = 0; i < avgSamples; i++)
  {
    sensorValue += analogRead(analogInPin);

    // wait 2 milliseconds before the next loop
    // for the analog-to-digital converter to settle
    // after the last reading:
    delay(2);
  }
  
  sensorValue = sensorValue / avgSamples;

  // The on-board ADC is 10-bits -> 2^10 = 1024 -> 5V / 1024 ~= 4.88mV
  // The voltage is in millivolts
  
  //voltage = 4.88 * sensorValue;
  hall_voltage = (sensorValue/1024.0) * 5000; // to get mV

  // This will calculate the actual current (in mA)
  // Using the Vref and sensitivity settings you configure
  current = (hall_voltage - Vref) / sensitivity;
  
  return current; 
}

float CheckTemp()
{
  float temperature;
  // Turn sensor on to start temperature measurement.
  // Current consumtion typically ~10uA.
  sensor0.wakeup();
  temperature = sensor0.readTempC(); // F for Fahrenheit
  // Place sensor in sleep mode to save power.
  // Current consumtion typically <0.5uA.
  sensor0.sleep();
  return temperature;
}

String DataRegister()
{ 
    String dataString = "";
//    for (int i = 0; i < 10; i++)
//    {
//      sensorValue += analogRead(analogInPin);
//    }
    dataString += String(CheckCurrent());
    //dataString += ",";
    
    //dataString += String(CheckVoltage());
    //dataString += ",";
    //dataString += String(CheckTemp());
    return dataString;
}

void SaveToFile(String dataString, String filename)
{
     filename.toCharArray(filechar,20);
     LFile dataFile = Drv.open(filechar, FILE_WRITE);

    // if the file is available, write to it:
    if (dataFile) 
      {
    dataFile.println(dataString);
    dataFile.close();
    // print to the serial port too:
      }
  // if the file isn't open, pop up an error:
     else 
     {
    Serial.println("error opening datalog.txt");
     }
     
}

void SaveCurrent ()
{
  
  for (int i = 0; i < CurrentValues[299]; i++)
  {
    if (i < (CurrentValues[299] - avgSamples))   // Validity check for case where  
    {                                           //there is no enough samples to form a sum from avgSamples
    for (int k = 0; k < avgSamples; k++)
    {
      sum += CurrentValues[i+k]; //To get the sample of values
    }
    i = i+ avgSamples;
    
    sensorValue = sum / avgSamples;
    sum = 0.0;

  // The on-board ADC is 10-bits -> 2^10 = 1024 -> 5V / 1024 ~= 4.88mV
  // The voltage is in millivolts
  
  //voltage = 4.88 * sensorValue;
  hall_voltage = (sensorValue/1024.0) * 5000; // to get mV

  // This will calculate the actual current (in mA)
  // Using the Vref and sensitivity settings you configure
  current = (hall_voltage - Vref) / sensitivity;
  //current = current / 1000;
  String dataString = "";
  dataString += String(current);
  SaveToFile(dataString, CurrentName[name_count]);
  }
  else if (i > (CurrentValues[299] - avgSamples))
  {
    //Do nothing
  }
  }
  // Save the lenght of the initial file used
  String dataString = "";
  dataString += String(CurrentValues[299]);
  SaveToFile(dataString, CurrentName[name_count]);
}

void SaveVoltage()
{
  for (int i = 0; i < VoltageValues[299]; i++)
  {
  String dataString = "";
   vout = (VoltageValues[i] * 5.0) / 1024.0; // see text
   vin = vout / (R2/(R1+R2));
   vin = vin * offset; 
   if (vin<0.09) 
   {
   vin=0.0;//statement to quash undesired reading !
   }
  dataString += String(vin);
  SaveToFile(dataString, VoltageName[name_count]);
  }
}

void TestRoutine()
{
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print("Test Initiated");
  delay(700);
  myservo.write(90);
  delay(1000);
  myservo.write(87);
  delay(500);
  myservo.write(84);
  delay(500);
  myservo.write(80); // Start motor
  delay(500);
  int i = 0;
  int ic = 0;
  int time_point = millis();
  float sum = 0;
  while ((millis()-time_point) < (routine_time/2))
  { 
    //SaveToFile(DataRegister());
    CurrentValues[i] = analogRead(analogInPin);
    i++;
    //Serial.println(analogRead(analogInPin));
  }
  CurrentValues[299] = i+1; // Write lenght of the values to the end of the array
  time_point = millis();
  i = 0;
    while ((millis()-time_point) < (routine_time/2))
  { 
    VoltageValues[i] = analogRead(A1);
    i++;
  }
  VoltageValues[299] = i+1; // Write lenght of the values to the end of the array
  myservo.write(84);
  delay(500);
  myservo.write(87);
  delay(500);
  myservo.write(90); // Stop motor 
  
  // Do calculations and save evertyhing to the file
  SaveCurrent();
  SaveVoltage();
  memset(CurrentValues,0,sizeof(CurrentValues)); // Clear the array
  memset(VoltageValues,0,sizeof(VoltageValues)); // Clear the array
  name_count++;
  if (name_count > 9)
  {
    name_count = 0; 
  }
  lcd.clear();
  lcd.print("Test Completed");
  delay(1500);
}

void TestRoutine2()
{
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print("Test Initiated");
  myservo.write(90); // Start motor
  delay(20);
  int i = 0;
  int ic = 0;
  int time_point = millis();
  float sum = 0;
  while ((millis()-time_point) < (routine_time/2))
  { 
    //SaveToFile(DataRegister());
    CurrentValues[i] = analogRead(analogInPin);
    i++;
    //Serial.println(analogRead(analogInPin));
  }
  delay(200);
  CurrentValues[299] = i+1; // Write lenght of the values to the end of the array
  time_point = millis();
  i = 0;
    while ((millis()-time_point) < (routine_time/2))
  { 
    VoltageValues[i] = analogRead(A1);
    i++;
  }
  VoltageValues[299] = i+1; // Write lenght of the values to the end of the array
  myservo.write(0); // Stop motor 
  delay(200);
  
  // Do calculations and save evertyhing to the file
  SaveCurrent();
  SaveVoltage();
  memset(CurrentValues,0,sizeof(CurrentValues)); // Clear the array
  memset(VoltageValues,0,sizeof(VoltageValues)); // Clear the array
  name_count++;
  if (name_count > 9)
  {
    name_count = 0; 
  }
  lcd.clear();
  lcd.print("Test Completed");
  delay(1500);
}

void ISR()
{
  measurement_flag = 1;
}






