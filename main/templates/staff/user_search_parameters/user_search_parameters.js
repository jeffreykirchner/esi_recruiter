axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";


var app = new Vue({

    delimiters: ['[[', ']]'],
    el: '#root',        
    data:{        
        experiment : {},
        recruitment_params:{{recruitment_params|safe}},
        recruitment_parameters_form_ids: {{recruitment_parameters_form_ids|safe}},
        confirmedCount:0,
        session:{confirmedCount:0},             //recruitment form parameter
        loading:true,
        buttonText1:"Search",                 //recruitment parameters update button text         
        working:false,          
        searchResults:[],
    },

    methods:{     

        //remove all the form errors
        clearMainFormErrors:function(){

            s = app.$data.recruitment_parameters_form_ids;
            for(var i in s)
            {
                $("#id_" + s[i]).attr("class","form-control");
                $("#id_errors_" + s[i]).remove();
            }
        },

        //update recruitment parameters 
        search: function(){           
            app.working = true;
            app.searchResults = [];
            document.getElementById("id_search_results").scrollIntoView();

            axios.post('{{ request.path }}', {
                    status :"search" ,                                
                    formData : this.recruitment_params,                                                              
                })
                .then(function (response) {     
                                                         
                    app.working = false;
                    status=response.data.status; 
                    app.clearMainFormErrors();

                    if(status=="success")
                    {                                 
                        app.searchResults = response.data.result.u_list_json;
                    }
                    else
                    {                                
                        app.displayErrors(response.data.errors);
                    }                          
                })
                .catch(function (error) {
                    console.log(error);
                    app.$data.searching=false;
                });                        
            },


        //if form is changed add * to button
        recruitmentFormChange:function(){
           
        },

        //displays to the form errors
        displayErrors:function(errors){
            for(var e in errors)
            {
                $("#id_" + e).attr("class","form-control is-invalid")
                var str='<span id=id_errors_'+ e +' class="text-danger">';
                
                for(var i in errors[e])
                {
                    str +=errors[e][i] + '<br>';
                }

                str+='</span>';
                $("#div_id_" + e).append(str);  

                var elmnt = document.getElementById("div_id_" + e);
                elmnt.scrollIntoView();   
            }
        },

        //show edit trait
        editTrait:function(index){

        },        
    },

    //run when vue is mounted
    mounted: function(){
        this.loading = false;
    },                 

});


