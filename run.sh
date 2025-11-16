#!/bin/bash

selenium-side-runner --server http://localhost:4444/wd/hub scenarios/*.side --output-directory=reports
