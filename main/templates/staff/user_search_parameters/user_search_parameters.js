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
        addTraitButtonText:'Add <i class="fas fa-plus fa-xs"></i>',
        updateTraitButtonText:'Update <i class="fas fa-sign-in-alt"></i>',
        current_trait:{
            id:0,
            trait_id:0,
            min_value:0,
            max_vaue:0,
            include_if_in_range:true,
        },  
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

        //add trait
        addTrait:function(){
            
        },

        //update trait
        updateTrait:function(){

            trait = app.getTraitById(app.current_trait.id);
            trait.min_value = app.current_trait.min_value;
            trait.max_value = app.current_trait.max_value;
            trait.trait_id = app.current_trait.trait_id;
            trait.include_if_in_range = app.current_trait.include_if_in_range;

            e = document.getElementById('id_trait');            
            trait.trait_name = e.options[e.selectedIndex].text;

            $('#updateTraitModal').modal('toggle');
        },

        //delete trait
        deleteTrait:function(id){
            
        },  
        
        //fire when edit trait model needs to be shown
        showEditTraits:function(){
            
            $('#editTraitsModal').modal('show');
            //app.clearMainFormErrors();
        },

        //fire when hide edit traits
        hideEditTraits:function(){
            
        },

        // fire when edit trait model is shown
        showUpdateTrait:function(id, index){

            tc = app.recruitment_params.trait_constraints[index];

            app.cancelModal=true;
            app.current_trait.id = id;
            app.current_trait.min_value = tc.min_value;
            app.current_trait.max_value = tc.max_value;
            app.current_trait.trait_id = tc.trait_id;
            app.current_trait.include_if_in_range = tc.include_if_in_range;

            $('#updateTraitModal').modal('show');
            app.clearMainFormErrors();
        },

        getTraitById(id){
            for(let i=0; i<app.recruitment_params.trait_constraints.length; i++)
            {
                if(app.recruitment_params.trait_constraints[i].id == id){
                    return app.recruitment_params.trait_constraints[i];
                }
            }

            return null;
        },

        //fire when edit experiment model hides, cancel action if nessicary
        hideUpdateTrait:function(){
            if(app.$data.cancelModal)
            {
               
            }
        },

    },

    //run when vue is mounted
    mounted: function(){
        this.loading = false;
        $('#editTraitsModal').on("hidden.bs.modal", this.hideEditTraits);
        $('#updateTraitModal').on("hidden.bs.modal", this.hideUpdateTrait);
    },                 

});


