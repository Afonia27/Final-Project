'use strict';

 function enter(args, ctx) {
 	window.AWSIotData.getThingShadow({ thingName: 'box' }, (error, data) => {
 		if (error) {
 			console.error('Error getting state', error);

 			return ctx.transitions.failure();
 		}

 		const payload = JSON.parse(data.payload);

 		ctx.behaviorData.yRotation = payload.state.reported.y_rotation;

 		ctx.transitions.success();
 	});
 }

function exit(args, ctx) {
}

 var parameters = [];