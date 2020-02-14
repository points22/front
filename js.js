
/* ************************************
 * ************* REQUESTS *************
 * *************************************/

var API_HOST = "https://pointsdb.lovemail.life";
var local = false;

if (window.location.href.indexOf("127.0.0.1:8888") > -1) {
	API_HOST = "http://127.0.0.1:5000"
	local = true;
}

function get(path, query, callback) {
	let retry = function() { get(path, query, callback); }
	var url = API_HOST + path;

	if(query) {
		url += '?' + jQuery.param(query);
	}

	console.log(url);

	jQuery.get(url, function( data ) {
	  console.log({response: data, callback: callback});
		if(callback)
			callback(data);
	}).fail(function() {
    if(confirm('Communication error. Retry?'))
			retry();
	});
}

function getPoints(callback, offset, limit) {
	query = {}
	if(offset) {
		query.offset = offset
	}
	if(limit) {
		query.limit = limit
	}
	return get(`/point`, query, callback);
}

function createPoint(point, callback) {
	return get('/point/create', point, callback);
}

function auth_check(callback) {
	return get(`/auth_check`, null, callback)
}

function deletePoint(id, callback) {
	return get(`/point/delete`, {id: id}, callback)
}

function auth_start(email, callback) {
	return get(`/auth_start`, {email: email}, callback);
}

function auth_finish(code, callback) {
	return get(`/auth_finish`, {code: code}, callback)
}

/* ************************************
 * ************** MAIN *****************
 * *************************************/

let pointerId = 0;
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
		// if ($('.pointer').length > 5) {

	// $('.pointer').each(function(){
	// 	let opacity = parseFloat($(this).css('opacity'));
	// 	opacity -= 0.1;		if (opacity <= 0) {
	// 		$(this).remove();
	// 	} else {
	// 		$(this).css('opacity', opacity);
	// 	}
	// });
		// }

	$('#point-' + pointerId + ' textarea').val(text);
	pointerId++;
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

});

// $('body').on('keypress',function(e) {
//   if(e.which == 13) {
// 		let text = $('#point-' + (newPoint.pointerId - 1) + ' textarea');
// 		$('#point-' + (newPoint.pointerId - 1) + ' textarea').trigger('blur');
// 		newPoint.text = text.val();
// 		console.log(newPoint);
// 		createPoint(newPoint);
//   }
// });



$('body').on('click', '.pointer', function(e){
	e.stopPropagation();

	$(this).css('opacity', '0.2');
});

function load_points() {
	load = function(arr) {
		arr.forEach(function(p) {
			console.log(p);
			drawPoint(p.x, p.y, p.text);
		});
		pointerId++;
		console.log('loaded points');
	$('body').on('blur', 'textarea',function(e) {
		let text = $(this)
		// $('#point-' + (newPoint.pointerId - 1) + ' textarea').trigger('blur');
		if (text.val() === '') {
			return ;
		}
		newPoint.text = text.val();
		console.log(newPoint);
		createPoint(newPoint);
	});
	}

	loader = function(data) {
		if(data.points) {
			load(data.points)
			// if(data.more) {
			// 	getPoints(loader, data.points.length);
			// }
		}
	}

	getPoints(loader);
}

$(document).ready(function() {

	if (!local && window.location.href.indexOf("https://") != 0) {
		window.location.href = "https://lovemail.life";
		return;
	}

	$.ajaxSetup({xhrFields: { withCredentials: true } });

	auth_check(function(data) {
		if(data.result) {
			alert(`Hello! Click OK to load your points`);
			load_points();
			return;
		}

		let email = prompt('Enter your email');
		auth_start(email, function(data) {
			if(!data.result) {
				alert('ERROR starting auth');
				return
			}

			let code = prompt('Check your email. Enter the code below!');
			auth_finish(code, function(data) {
				if(data.result) {
					console.log('auth_success')
					load_points();
					return;
				}
				alert('FAIL. Wrong code? Reload page.');
			});

		});
	});

});
