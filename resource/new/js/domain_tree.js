// 设置margin参数
var margin = { top: 20, right: 120, bottom: 20, left: 120 },
    width = 960 - margin.right - margin.left,
    height = 720 - margin.top - margin.bottom;

var duration = 750,
    root, TREE_I = 0;

// 查询的根域名
var ROOT_NAME;


// 构建一颗树
var tree = d3.layout.tree()
    .size([height, width]);


var diagonal = d3.svg.diagonal()
    .projection(function (d) { return [d.y, d.x]; });

var svg = d3.select("#tree_domain_svg").append("svg")
    .attr("width", width + margin.right + margin.left)
    .attr("height", height + margin.top + margin.bottom)
    .style("overflow", "scroll")
    .append("g").attr("class", "drawarea")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

var loop = 0;

d3.select(self.frameElement).style("height", "720px");

function update(source) {

    // Compute the new tree layout.
    var nodes = tree.nodes(root).reverse(),
        links = tree.links(nodes);

    // Normalize for fixed-depth.
    nodes.forEach(function (d) { d.y = d.depth * 180; });

    // Update the nodes…
    var node = svg.selectAll("g.node")
        .data(nodes, function (d) { return d.id || (d.id = ++TREE_I); });

    // Enter any new nodes at the parent's previous position.
    var nodeEnter = node.enter().append("g")
        .attr("class", "node")
        .attr("transform", function (d) {console.log(source.y0,source.x0); return "translate(" + source.y0 + "," + source.x0 + ")"; })
        .on("click", click);

    nodeEnter.append("circle")
        .attr("r", 1e-6)
        .style("fill", function (d) { return d._children ? "lightsteelblue" : "#fff"; });

    nodeEnter.append("text")
        .attr("x", function (d) { return d.children || d._children ? -10 : 10; })
        .attr("dy", ".35em")
        .attr("text-anchor", function (d) { return d.children || d._children ? "end" : "start"; })
        .text(function (d) { return d.name; })
        .style("fill-opacity", 1e-6);

    // Transition nodes to their new position.
    var nodeUpdate = node.transition()
        .duration(duration)
        .attr("transform", function (d) { return "translate(" + d.y + "," + d.x + ")"; });

    nodeUpdate.select("circle")
        .attr("r", 7.5)
        .style("fill", function (d) { return d._children ? "lightsteelblue" : "#fff"; });

    nodeUpdate.select("text")
        .style("fill-opacity", 1);

    // Transition exiting nodes to the parent's new position.
    var nodeExit = node.exit().transition()
        .duration(duration)
        .attr("transform", function (d) { console.log(source.y, source.x); return "translate(" + source.y + "," + source.x + ")"; })
        .remove();

    nodeExit.select("circle")
        .attr("r", 1e-6);

    nodeExit.select("text")
        .style("fill-opacity", 1e-6);

    // Update the links…
    var link = svg.selectAll("path.link")
        .data(links, function (d) { return d.target.id; });

    // Enter any new links at the parent's previous position.
    link.enter().insert("path", "g")
        .attr("class", "link")
        .attr("d", function (d) {
            var o = { x: source.x0, y: source.y0 };
            return diagonal({ source: o, target: o });
        });

    // Transition links to their new position.
    link.transition()
        .duration(duration)
        .attr("d", diagonal);

    // Transition exiting nodes to the parent's new position.
    link.exit().transition()
        .duration(duration)
        .attr("d", function (d) {
            var o = { x: source.x, y: source.y };
            return diagonal({ source: o, target: o });
        })
        .remove();

    // Stash the old positions for transition.
    nodes.forEach(function (d) {
        d.x0 = d.x;
        d.y0 = d.y;
    });


    // 缩放应用
    // d3.select("svg").call(d3.behavior.zoom().scaleExtent([0.5, 5]).on("zoom", zoom));
}

function zoom() {
    var scale = d3.event.scale,
        translation = d3.event.translate,
        tbound = -height * scale,
        bbound = height * scale,
        lbound = (-width + margin.right) * scale,
        rbound = (width - margin.left) * scale;

    translation = [
        Math.max(Math.min(translation[0], rbound), lbound),
        Math.max(Math.min(translation[1], bbound), tbound)
    ];
    d3.select(".drawarea")
        .attr("transform", "translate(" + translation + ")" +
        " scale(" + scale + ")");
}


// Toggle children on click.
function click(d) {
    if (d.children) {
        d._children = d.children;
        d.children = null;
    } else {
        d.children = d._children;
        d._children = null;
    }
    update(d);
}

function appendData(_root_name, domainInfos) {
    // 先隐藏后面的元素
    console.log(JSON.stringify(domainInfos))
    function collapse(d) {
        if (d.children && d.children > 5) {
            if (d.children) {
                d._children = d.children;
                d._children.forEach(collapse);
                d.children = null;
            }
        }
    }

    function _init() {
        ROOT_NAME = _root_name;
        root = { 'name': _root_name, 'children': [] };
        root.x0 = height / 2;
        root.y0 = 0;
        domainInfos.forEach(formatData);
        root.children.forEach(collapse);
        update(root);
    }

    function addData(d) {
        var ip = d.ip;
        var subdomain = d.subdomain;
        var isAdd = false;
        d3.selectAll('g.node').each(function (node_d) {
            if (node_d.name == ip) {
                if (node_d.children) {
                    node_d.children.push({ "name": subdomain, "size": 1, 'children': [] });
                    if (node_d.children.length > 5) {
                        node_d._children = node_d.children
                        node_d.children = null
                    }
                } else {
                    node_d._children.push({ "name": subdomain, "size": 1, 'children': [] });
                }

                isAdd = true;
                console.log("this")
                update(this);
            }

        });

        if (!isAdd) {
            d3.selectAll('g.node').each(function (node_d) {
                if (node_d.children || node_d._children) {

                    if (node_d.name == ROOT_NAME) {
                        if (node_d.children) {
                            node_d.children.push({ "name": ip, "size": 1, 'children': [{ "name": subdomain, "size": 1, 'children': [] }] });
                        } else {
                            node_d._children.push({ "name": ip, "size": 1, 'children': [{ "name": subdomain, "size": 1, 'children': [] }] });
                        }

                        isAdd = true;
                        update(this);
                    }
                }
            });
        }
    }

    // 格式化数据
    function formatData(d) {
        var ip = d.ip;
        var subdomain = d.subdomain;
        var isAdd = false;

        if (root.name == ip) {
            root.children.push({ 'name': subdomain, "size": 1 })
            return;
        }

        for (i = root.children.length - 1; i >= 0; i--) {

            if (root.children[i].name == ip) {
                if (root.children[i].children) {
                    root.children[i].children.push({ "name": subdomain, "size": 1, '_children': [] });
                } else {
                    root.children[i]._children.push({ "name": subdomain, "size": 1, '_children': [] });
                }



                isAdd = true;
            }
        }

        if (!isAdd) {
            root.children.push({ 'name': ip, "size": 1, 'children': [{ "name": subdomain, "size": 1 }] })
        }
    }

    if (!root) {
        _init();
    } else {
        domainInfos.forEach(addData);
    }
}





    /**
    appendData("313.131.111.11",[{"ip":'313.131.111.11','subdomain':'hr1.cxhr.com'}])
    appendData("313.131.111.11",[{"ip":'313.131.111.11','subdomain':'hr2.cxhr.com'}])
    appendData("313.131.111.11",[{"ip":'313.131.111.11','subdomain':'hr3.cxhr.com'}])
    appendData("313.131.111.11",[{"ip":'313.131.111.11','subdomain':'hr4.cxhr.com'}])
    appendData("313.131.111.11",[{"ip":'313.131.111.11','subdomain':'hr5.cxhr.com'}])
    appendData("313.131.111.11",[{"ip":'313.131.111.11','subdomain':'hr6.cxhr.com'}])
     **/
