"""
All classes for conversions are defined below:
 each class should have one method for converting "to_base and another for converting "from_base"
the return value is the converted value to or from base
"""


import evil_globals


# used for Computer numbers base definitions.
ALPHA_NUMERIC = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'


def makeBase(x, base = len(ALPHA_NUMERIC), table=ALPHA_NUMERIC):
	"""
	Convert from base 10 to any other base.
	>> makeBase(1, 10)
	'1'
	>> makeBase(11, 10)
	'11'
	>> makeBase(11, 16)
	'b'
	"""
	d, m = divmod(x, base)
	if not d:
		return table[m]
	return makeBase(d, base, table) + table[m]


# roman numerals
roman_group = {
	1: ('i','v'),
	10: ('x','l'),
	100: ('c','d'),
	1000: ('m','A'),
	10000: ('B','C'),
}


# functions that convert Arabic digits to roman numerals
roman_value = {
	0: lambda i,v,x: '',
	1: lambda i,v,x: i,
	2: lambda i,v,x: i+i,
	3: lambda i,v,x: i+i+i,
	4: lambda i,v,x: i+v,
	5: lambda i,v,x: v,
	6: lambda i,v,x: v+i,
	7: lambda i,v,x: v+i+i,
	8: lambda i,v,x: v+i+i+i,
	9: lambda i,v,x: i+x,
}


def toroman(n):
	"""
	convert a decimal number in [1,4000) to a roman numeral
	>>> toroman(0)
	>>> toroman(4001)
	>>> toroman(1)
	'i'
	>>> toroman(4)
	'iv'
	>>> toroman(5)
	'v'
	>>> toroman(10)
	'x'
	>>> toroman(15)
	'xv'
	"""
	if n < 0:
		raise NotImplemented("Value out of roman comprehension")
	elif n == 0:
		''
	elif n >= 4000:
		raise NotImplemented("Value Out of Range")

	base = 1
	s = ''
	while n > 0:
	    i,v = roman_group[base]
	    base = base * 10
	    x,l = roman_group[base]
	    digit = n % 10
	    n = (n-digit)/10
	    s = roman_value[digit](i,v,x) + s
	return s


def fromroman(s, rbase = 1):
	"""
	convert a roman numeral (in lowercase) to a decimal integer
	>>> fromroman('')
	0
	>>> fromroman('x')
	5
	>>> fromroman('xv')
	15
	"""
	if len(s) == 0:
	    return 0
	elif rbase > 1000:
	    return 0

	i, v = roman_group[rbase]
	x, l = roman_group[rbase*10]
	conversions = [
		(v+i+i+i, 8),
		(i+i+i+i, 5),
		(v+i+i, 7),
		(i+i+i, 3),
		(v+i, 6),
		(i+x, 9),
		(i+v, 4),
		(i+i, 2),
		(i, 1),
		(v, 5),
	]
	for conversion in conversions:
		if s.endswith(conversion[0]):
			digit = conversion[1]
			s = s[:-len(conversion[0])]
			break
	else:
		digit = 0
		s = s

	return digit * rbase + fromroman(s, rbase*10)


class simple_multiplier(object):

	def to_base(self,value,multiplier):
		return value * (multiplier)

	def from_base(self,value,multiplier):
		if multiplier == 0:
			return 0.0
		else:
			return value / (multiplier)


class simple_inverter(object):

	def to_base(self,value,multiplier):
		if value == 0:
			return 0.0
		else:
			return (multiplier) / value

	def from_base(self,value,multiplier):
		if value == 0:
			return 0.0
		else:
			return (multiplier) / value


class simple_gain_offset(object):

	def to_base(self,value,(gain,offset)):
		return (value * (gain)) + offset

	def from_base(self,value,(gain,offset)):
		if gain == 0:
			return 0.0
		else:
			return (value - offset) / gain


class simple_offset_gain(object):

	def to_base(self,value,(offset,gain)):
		return (value + offset) * gain

	def from_base(self,value,(offset,gain)):
		if gain == 0:
			return 0.0
		else:
			return (value / gain) - offset


class slope_offset(object):
	''"convert using points on a graph''"

	def to_base(self,value,((low_in,high_in),(low_out,high_out))):
		gain = (high_out-low_out)/(high_in-low_in)
		offset = low_out - gain*low_in
		return gain*value+offset

	def from_base(self,value,((low_out,high_out),(low_in,high_in))):
		gain = (high_out-low_out)/(high_in-low_in)
		offset = low_out - gain*low_in
		return gain*value+offset


class double_slope_offset(object):
	''"convert using points on a graph, graph split into two slopes''"

	def to_base(self,value,((low1_in,high1_in),(low1_out,high1_out),(low2_in,high2_in),(low2_out,high2_out))):
		if low1_in<=value<=high1_in:
			gain = (high1_out-low1_out)/(high1_in-low1_in)
			offset = low1_out - gain*low1_in
			return gain*value+offset
		if low2_in<=value<=high2_in:
			gain = (high2_out-low2_out)/(high2_in-low2_in)
			offset = low2_out - gain*low2_in
			return gain*value+offset
		return 0.0

	def from_base(self,value,((low1_in,high1_in),(low1_out,high1_out),(low2_in,high2_in),(low2_out,high2_out))):
		if low1_out<=value<=high1_out:
			gain = (high1_in-low1_in)/(high1_out-low1_out)
			offset = low1_in - gain*low1_out
			return gain*value+offset
		if low2_out<=value<=high2_out:
			gain = (high2_in-low2_in)/(high2_out-low2_out)
			offset = low2_in - gain*low2_out
			return gain*value+offset
		return 0.0


class base_converter(object):

	def to_base(self,value,base):
		"""
		Convert from any base to base 10 (decimal)
		"""
		result = 0L #will contain the long base-10 (decimal) number to be returned
		position = len(value) #length of the string that is to be converted
		for x in value:
			position = position-1
			result = long(result + long(long(string.find(ALPHA_NUMERIC,x))*(long(base)**long(position))))
		return result

	def from_base(self,value,base):
		"""
		Convert from decimal to any base
		"""
		return makeBase(value,base)


class roman_numeral(object):

	def to_base(self,value,junk):
		"""
		Convert from roman numeral to base 10 (decimal)
		"""
		if value=="0":
			return 0L
		else:
			return fromroman(value)

	def from_base(self,value,junk):
		"""
		Convert from decimal to roman numeral
		"""
		return toroman(value)



class function(object):
	''"defined simple function can be as complicated as you like, however, both to/from base must be defined.''"

	#value is assumed to be a string
	#convert from a defined function to base
	def to_base(self,value,(to_base,from_base)):
		exec "y="+to_base[:string.find(to_base,'x')]+str(value)+to_base[string.find(to_base,'x')+1:]
		return y

	def from_base(self,value,(to_base,from_base)):
		exec "y="+from_base[:string.find(from_base,'x')]+str(value)+from_base[string.find(from_base,'x')+1:]
		return y


#--------- function definitions from classes ------------
m = simple_multiplier()
inv = simple_inverter()
gof = simple_gain_offset()
ofg = simple_offset_gain()
slo = slope_offset()
dso = double_slope_offset()
b = base_converter()
r = roman_numeral()
f = function()
