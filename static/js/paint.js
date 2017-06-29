var height = "800px",
    width = "100%"

var svg = d3.select("#svg")
    .append("svg")
    .attr("width", width)
    .attr("height", height)

var gTree = svg.append("g")
    .attr("transform", "translate(350,50)")


var margin = { top: 20, right: 120, bottom: 20, left: 120 },
    width = 960 - margin.right - margin.left,
    height = 720 - margin.top - margin.bottom;

var tree = d3.layout.tree()
    .size([height, width])
    .separation(function (a, b) {
        return a.parent == b.parent ? 1 : 2
    })

var diagonal = d3.svg.diagonal()
    .projection(function (d) { return [d.y, d.x] })

d3.textBlock = function () { 

    var label = "";

    function my(selection) {
        console.log('fuck')
        selection.each(function (d, i) {
            var labelvar = (typeof (label) === "function" ? label(d) : label);

            var element = d3.select(this);

            var strs = labelvar.split(" ")
            var el = []
            strs.length > 1 ? el.push(strs[0], strs.slice(1)) : el = strs
            // first append text to svg:g

            var t = element.append("text")
                .attr("font-size", "12px")
                .attr("x", 0)
                // .attr("y", "-1em")


            if(el.length === 1) {
                t.text(labelvar)
                .attr("y", "0")
                .attr("fill", "white")
                .attr("dominant-baseline", "central")
            } else {
                t.attr("y", "-1em")
                t.selectAll("tspan")
                    .data(el)
                    .enter()
                    .append("tspan")
                    .attr("x", "0")
                    .attr("dy", "1em")
                    .attr("fill", "white")
                    .text(function (d) {
                        return d;
                    });
            }

            var bb = t[0][0].getBBox();

            var className = ""
            if(labelvar === "NS") {
                className = "domain"
            } else if(labelvar === "MX") {
                className = "ip"
            } else if(labelvar === "site") {
                className = "site"
            } else {
                className = "child"
            }
            element.append("rect")
                .attr("x", -5)
                .attr("y", - bb.height * 0.75)
                .attr("width", bb.width + 10)
                .attr("height", bb.height * 1.5)
                .attr("class", className)
                .attr("fill", "steelblue")
                .attr("fill-opacity", 1)
                .attr("stroke-width", 1);

            var t2 = element.append("text")
                .attr("font-size", "12px")
                .attr("color", "white")
                .attr("x", 0)
                // .attr("y", "-1em")

            if(el.length === 1) {
                t2.text(labelvar)
                    .attr("y", "0")
                    .attr("fill", "white")
                    .attr("dominant-baseline", "central")
            } else {
                t2.attr("y", "-1em")
                t2.selectAll("tspan")
                    .data(el)
                    .enter()
                    .append("tspan")
                    .attr("x", "0")
                    .attr("dy", "1em")
                    .attr("fill", "white")
                    .attr("class", "tspan")
                    .text(function (d) {
                        return d;
                    });
            }
            
        })

    }

    my.label = function (value) {
        if (!arguments.length) return value;
        label = value;
        return my;
    };

    return my;
}

var tb = d3.textBlock().label(function (d) { return d.name; });


function svgPaint(root) {
    root = JSON.parse(root)
    var nodes = tree.nodes(root)
    var links = tree.links(nodes)

    // console.log(nodes)
    // console.log(links)

    var link = gTree.selectAll(".link")
        .data(links)
        .enter()
        .append("path")
        .attr("class", "link")
        .attr("d", diagonal)

    var node = gTree.selectAll(".node")
        .data(nodes)
        .enter()
        .append("g")
        .attr("class", "node")
        .attr("transform", function (d) {
            return "translate(" + d.y + "," + d.x + ")"
        })
        .call(tb)
}