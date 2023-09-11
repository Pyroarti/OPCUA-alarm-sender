# OPC UA Alarm Monitor with SMS Notification
## Overview
This project aims to serve as an alarm monitoring system that observes an OPC UA (Open Platform Communications Unified Architecture) server and sends out SMS notifications to registered users in case of triggered events. The solution combines Python's Flask web framework for the user interface and the asyncua library for the OPC UA client.

## Features
Monitoring an OPC UA server for alarms or specific events.
Sending SMS notifications to registered phone numbers via a GSM modem connected to a Raspberry Pi.
Flask-based web interface to manage users (add, edit, delete phone numbers).
Threaded execution of the Flask web server and the OPC UA client to run concurrently.

## Dependencies  
Flask  
asyncua  
asyncio  
Python's serial library  
Python's threading  
