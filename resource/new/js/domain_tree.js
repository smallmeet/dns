d3.textBlock = function () {

    var label = "";

    function my(selection) {
        selection.each(function (d, i) {
            var labelvar = (typeof (label) === "function" ? label(d) : label);

            var element = d3.select(this);

            var strs = labelvar.split(" ")
            // first append text to svg:g

            var t = element.append("text")
                .attr("font-size", "12px")
                .attr("x", 0)
            // .attr("y", "-1em")


            if (strs.length === 1) {
                t.text(labelvar)
                    .attr("y", "0")
                    .attr("fill", "white")
                    .attr("dominant-baseline", "central")
            } else {
                t.attr("y", "-1em")
                t.selectAll("tspan")
                    .data(strs)
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
            if (labelvar === "NS") {
                className = "ns"
            } else if (labelvar === "MX") {
                className = "mx"
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

            if (strs.length === 1) {
                t2.text(labelvar)
                    .attr("y", "0")
                    .attr("fill", "white")
                    .attr("dominant-baseline", "central")
            } else {
                t2.attr("y", "-1em")
                t2.selectAll("tspan")
                    .data(strs)
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
function domainPaint(root, width, height) {
    root = JSON.parse(root)

    var totalNodes = 0;
    var maxLabelLength = 0;
    var i = 0;
    var duration = 750;
    var root;

    // size of the diagram
    var viewerWidth = $(document).width();
    var viewerHeight = height;

    var tree = d3.layout.tree()
    // .size([viewerHeight, viewerWidth]);

    var diagonal = d3.svg.diagonal()
        .projection(function (d) {
            return [d.y, d.x];
        });


    function visit(parent, visitFn, childrenFn) {
        if (!parent) return;

        visitFn(parent);

        var children = childrenFn(parent);
        if (children) {
            var count = children.length;
            for (var i = 0; i < count; i++) {
                visit(children[i], visitFn, childrenFn);
            }
        }
    }

    visit(root, function (d) {
        totalNodes++;
        maxLabelLength = Math.max(d.name.length, maxLabelLength);

    }, function (d) {
        return d.children && d.children.length > 0 ? d.children : null;
    });

    var baseSvg = d3.select("#svg").append("svg")
        .attr("width", viewerWidth)
        .attr("height", viewerHeight)
        .attr("class", "overlay")

    function update(source) {
        var levelWidth = [1];
        var childCount = function (level, n) {

            if (n.children && n.children.length > 0) {
                if (levelWidth.length <= level + 1) levelWidth.push(0);

                levelWidth[level + 1] += n.children.length;
                n.children.forEach(function (d) {
                    childCount(level + 1, d);
                });
            }
        };
        childCount(0, root);
        var newHeight = d3.max(levelWidth) * 40; // 25 pixels per line  
        tree = tree.size([newHeight, viewerWidth]);

        var nodes = tree.nodes(root).reverse(),
            links = tree.links(nodes);

        nodes.forEach(function (d) {
            d.y = (d.depth * (maxLabelLength * 10)); //maxLabelLength * 10px
            
        });

        node = svgGroup.selectAll("g.node")
            .data(nodes, function (d) {
                return d.id || (d.id = ++i);
            });

        var nodeEnter = node.enter().append("g")
            .attr("class", "node")
            .attr("transform", function (d) {
                return "translate(" + source.y0 + "," + source.x0 + ")";
            })
            .call(tb)

        var nodeUpdate = node.transition()
            .duration(duration)
            .attr("transform", function (d) {
                return "translate(" + d.y + "," + d.x + ")";
            });

        var link = svgGroup.selectAll("path.link")
            .data(links, function (d) {
                return d.target.id;
            });

        link.enter().insert("path", "g")
            .attr("class", "link")
            .attr("d", function (d) {
                var o = {
                    x: source.x0,
                    y: source.y0
                };
                return diagonal({
                    source: o,
                    target: o
                });
            });

        link.transition()
            .duration(duration)
            .attr("d", diagonal);

        
        nodes.forEach(function (d) {
            d.x0 = d.x;
            d.y0 = d.y;
        });
    }

    var svgGroup = baseSvg.append("g")
    .attr("transform", "translate(350,20)")

    root.x0 = viewerHeight / 2;
    root.y0 = 0;

    update(root);
}
