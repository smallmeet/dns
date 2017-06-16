/**
 * Created by killua on 16-9-1.
 */
var index = 0;
var myalert = function(content,id){
    if(document.getElementById("0") == undefined){
        var newalert = document.createElement("div");
        newalert.id = 0;
        if(id == "tipright"){
            newalert.innerHTML = '<i class="icon-ok-sign" style="font-size:18px;margin-right:5px;"></i>'+content+'<i class="fa fa-remove remove" style="float:right;cursor:pointer;"></i>'
        }else{
            newalert.innerHTML = '<i class="icon-exclamation-sign" style="font-size:18px;margin-right:5px;"></i>'+content+'<i class="fa fa-remove remove" style="float:right;cursor:pointer;"></i>'
        }
        // newalert.innerHTML = '<i class="fa  fa-check-circle-o" style="font-size:18px;margin-right:5px;"></i>'+content+'<i class="fa fa-remove remove" style="float:right;cursor:pointer;"></i>'
        newalert.style.display = "block";
        newalert.style.position = "fixed";
        newalert.style.top = "58%";
        newalert.style.left = "50%";
        newalert.style.marginLeft = "-175px";
        newalert.style.width = "350px";
        if(id == "tipright"){
            newalert.style.background = "#51a351";
        }else{
            newalert.style.background = "#bd362f";
        }
        newalert.style.opacity = "0.8";
        newalert.style.boxShadow = "0 0 12px #999";
        newalert.style.color = "white";
        newalert.style.fontSize = "16px";
        newalert.style.lineHeight = "1.5";
        newalert.style.padding = "10px";
        newalert.style.borderRadius = "2px";
        newalert.style.zIndex = "1060";
        document.body.appendChild(newalert);
        setTimeout('jQuery("#0").css("display","none");',1500);
        jQuery(".remove").click(function(){
            jQuery("#0").css("display","none");
        });
    }else{
        document.getElementById("0").innerHTML = "";
        if(id == "tipright"){
            document.getElementById("0").innerHTML = '<i class="icon-ok-sign" style="font-size:18px;margin-right:5px;"></i>'+content+'<i class="fa fa-remove remove" style="float:right;cursor:pointer;"></i>'
        }else{
            document.getElementById("0").innerHTML = '<i class="icon-exclamation-sign" style="font-size:18px;margin-right:5px;"></i>'+content+'<i class="fa fa-remove remove" style="float:right;cursor:pointer;"></i>'
        }
        if(id == "tipright"){
            document.getElementById("0").style.background = "#51a351";
        }else{
            document.getElementById("0").style.background = "#bd362f";
        }
        document.getElementById("0").style.display = "block";
        setTimeout('jQuery("#0").css("display","none");',1500);
        jQuery(".remove").click(function(){
            jQuery("#0").css("display","none");
        });
    }
    index++;
};