    function deactivate_all()
    {
      $$( "#dialog-confirm" ).dialog({
          resizable: false,
          height:200,
          width:480,
          modal: true,
          buttons: {
            "Deactivate all items": function() {
            $$( this ).dialog( "close" );
          },
          Cancel: function() {
            $$( this ).dialog( "close" );
          }
        }
      });
    }


