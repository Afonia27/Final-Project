 'use strict';

  function enter(args, ctx) {
	  var entityDiv = document.getElementById('intersection-entity');
  	try {
		if (ctx.behaviorData.yRotation == "red") {
		// Color is a 4 component array in the order: red, green, blue, alpha
        const redColor = [1, 0, 0, 0];
        ctx.entity.setDiffuse(redColor);
		entityDiv.innerHTML = 'Oxygen Sensor is unavailiable';
		//sumerian.SystemBus.emit('Error');
		}
		else if (ctx.behaviorData.yRotation == "white") {
		// Color is a 4 component array in the order: red, green, blue, alpha
        const whiteColor = [0.31, 0.29, 0.29, 0];
        ctx.entity.setDiffuse(whiteColor);
		entityDiv.innerHTML = 'Fully Operational';
		//sumerian.SystemBus.emit('NoError');
		}
  	} catch (error) {
  		console.error('Error rotating box', error);

  		return ctx.transitions.failure();
  	}

  	ctx.transitions.success();
  }

  function exit(args, ctx){}

  //Converts from degrees to radians
  Math.radians = function(degrees) {
    return degrees * Math.PI / 180;
  };

  var parameters = [];
