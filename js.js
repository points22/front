let pointerId = 0;

function getPoints(callback) {
	jQuery.get( "http://localhost:5000/point", function( data ) {
	  console.log({
			response: data,
		});
		data = JSON.parse(data);
		callback(data);
	})
}

function createPoint(point) {
	jQuery.get(`http://localhost:5000/point/create?x=${point.x}&y=${point.y}&text=${point.text}`, function( data ) {
	  console.log({
			response: data,
		});
	});
}

var newPoint = {x: 0, y: 0, text: null, pointerId: 0};

function drawPoint(xPos, yPos, text) {
	// $(this).append('<div id="point-'+pointerId+'" class="pointer"><div class="pointer-in-circle"><input type="text"/></div></div>');
	$('body').append('<div id="point-'+pointerId+'" class="pointer"><div class="pointer-in-circle"><textarea maxlength="140" rows="1"></textarea></div></div>');
	if (xPos + 100 > $(window).width()){
		// $('#point-' + pointerId).css('transform', 'rotate(90deg)');
		$('#point-' + pointerId).addClass('vertical');
	}
	if (xPos - 100 < 0) {
		$('#point-' + pointerId).addClass('vertical');
		// $('#point-' + pointerId).css('transform', 'rotate(-90deg)');
	}
	$('#point-' + pointerId).css('left', xPos + 'px');
	$('#point-' + pointerId).css('top', yPos + 'px');
	$('#point-' + pointerId + ' textarea').trigger('focus');
		if ($('.pointer').length > 5) {

	$('.pointer').each(function(){
		let opacity = parseFloat($(this).css('opacity'));
		opacity -= 0.1;
		$(this).css('opacity', opacity);
	});
		}

	$('#point-' + pointerId + ' textarea').val(text);
}

$('body').click(function (e) {
	if ($('.pointer').has(e.target).length !== 0) {
		return ;
	}

	drawPoint(e.pageX, e.pageY, "");

	newPoint.x = e.pageX;
	newPoint.y = e.pageY;
	newPoint.text = null;
	newPoint.pointerId = pointerId;

	pointerId++;
});


$('body').on('keypress',function(e) {
  if(e.which == 13) {
		let text = $('#point-' + newPoint.pointerId + ' textarea');
		newPoint.text = text.val();
		console.log(newPoint);
		createPoint(newPoint);
  }
});


$('body').on('click', '.pointer', function(e){
	e.stopPropagation();

	// $(this).css('opacity', '0.2');
});

$(document).ready(function() {
	getPoints(function(arr) {
		arr.forEach(function(p) {
			console.log(p);
			drawPoint(p.x, p.y, p.text);
		});
		pointerId++;
		console.log('loaded points');
	});
});
