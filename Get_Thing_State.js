{\rtf1\ansi\ansicpg1252\cocoartf1561\cocoasubrtf600
{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww10800\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 'use strict';\
\
 function enter(args, ctx) \{\
 	window.AWSIotData.getThingShadow(\{ thingName: 'box' \}, (error, data) => \{\
 		if (error) \{\
 			console.error('Error getting state', error);\
\
 			return ctx.transitions.failure();\
 		\}\
\
 		const payload = JSON.parse(data.payload);\
\
 		ctx.behaviorData.yRotation = payload.state.reported.y_rotation;\
\
 		ctx.transitions.success();\
 	\});\
 \}\
\
function exit(args, ctx) \{\
\}\
\
 var parameters = [];}