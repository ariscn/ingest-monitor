
 $(document).ready(function() {
     $("#searchInput").keyup(function(){
         //hide all the rows
         $("#fbody").find("tr").hide();
         //split the current value of searchInput
         var data = this.value.split(" ");
         //create a jquery object of the rows
         var jo = $("#fbody").find("tr");
         //Recursively filter the jquery object to get results. 
         $.each(data, function(i, v){
             jo = jo.filter("*:contains('"+v+"')");
         });
         //show the rows that match.
         jo.show();
         //Removes the placeholder text 
     }).focus(function(){
         this.value="";
         $(this).css({"color":"black"});
         $(this).unbind('focus');
     }).css({"color":"#C0C0C0"});
 });
