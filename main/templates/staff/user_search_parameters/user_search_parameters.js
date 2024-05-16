axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";


var app = Vue.createApp({

    delimiters: ['[[', ']]'],
         
    data() {return{   
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
            trait:0,
            min_value:0,
            max_vaue:0,
            include_if_in_range:1,
        },  
        loginLast90Days:false,

        //modals
        editTraitsModal:null,
        updateTraitModal:null,
    }},

    methods:{     

        //remove all the form errors
        clearMainFormErrors:function clearMainFormErrors(){

            let s = app.recruitment_parameters_form_ids;
            for(var i in s)
            {
                let e = document.getElementById("id_errors_" + s[i]);
                if(e) e.remove();
            }
        },

        //update recruitment parameters 
        search: function search(){           
            app.working = true;
            app.searchResults = [];
            document.getElementById("id_search_results").scrollIntoView();

            axios.post('{{ request.path }}', {
                    status :"search" ,                                
                    formData : app.recruitment_params,          
                    trait_parameters : app.recruitment_params.trait_constraints,     
                    trait_constraints_require_all : app.recruitment_params.trait_constraints_require_all,  
                    login_last_90_days : app.loginLast90Days,                                        
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
                    app.searching=false;
                });                        
            },


        //if form is changed add * to button
        recruitmentFormChange:function recruitmentFormChange(){
           
        },

        //display form errors
        displayErrors: function displayErrors(errors){
            for(let e in errors)
            {
                let str='<span id=id_errors_'+ e +' class="text-danger">';
                
                for(let i in errors[e])
                {
                    str +=errors[e][i] + '<br>';
                }

                str+='</span>';

                document.getElementById("div_id_" + e).insertAdjacentHTML('beforeend', str);

                //scroll to the last error
                var elmnt =  document.getElementById("div_id_" + e);
                if(elmnt) elmnt.scrollIntoView();
            }
        },  

        //add trait
        addTrait:function addTrait(){

            var id = 0;
            
            // find highest id
            for(let i=0; i<app.recruitment_params.trait_constraints.length; i++)
            {
                if(app.recruitment_params.trait_constraints[i].id > id){
                    id = app.recruitment_params.trait_constraints[i].id;
                }
            }

            e = document.getElementById('id_trait');            
            e.selectedIndex = 1;

            trait = {"id":id+1,
                     "name": e.options[e.selectedIndex].text + " Inc. 0.00-10.00",
                     "trait_name":e.options[e.selectedIndex].text,
                     "trait":e.value,
                     "min_value":"0.00",
                     "max_value":"10.00",
                     "recruitment_parameter_id":0,
                     "include_if_in_range":1};
            
            app.recruitment_params.trait_constraints.push(trait);
        },

        //no action when changed
        updateRequireAllTraitContraints:function updateRequireAllTraitContraints(){
        },

        //update trait
        updateTrait:function updateTrait(){

            trait = app.getTraitById(app.current_trait.id);
            trait.min_value = Number(app.current_trait.min_value).toFixed(2);
            trait.max_value = Number(app.current_trait.max_value).toFixed(2);
            trait.trait = app.current_trait.trait;
            trait.include_if_in_range = app.current_trait.include_if_in_range;

            e = document.getElementById('id_trait');            
            if(e.selectedIndex == -1)
            {
                trait.trait_name = null;
            }
            else
            {
                trait.trait_name = e.options[e.selectedIndex].text;
            }
           
            let mode = trait.include_if_in_range ? "Inc." : "Exc.";
            trait.name = trait.trait_name + " " + mode + " " + trait.min_value + "-" + trait.max_value;

            app.updateTraitModal.toggle();
        },

        //delete trait
        deleteTrait:function deleteTrait(id){
            for(let i=0; i<app.recruitment_params.trait_constraints.length; i++)
            {
                if(app.recruitment_params.trait_constraints[i].id == id){
                    app.recruitment_params.trait_constraints.splice(i, 1);
                    return;
                }
            }
        },  
        
        //fire when edit trait model needs to be shown
        showEditTraits:function showEditTraits(){
            
            app.editTraitsModal.show();
            //app.clearMainFormErrors();
        },

        //fire when hide edit traits
        hideEditTraits:function hideEditTraits(){
            
        },

        // fire when edit trait model is shown
        showUpdateTrait:function showUpdateTrait(id, index){

            let tc = app.recruitment_params.trait_constraints[index];

            app.cancelModal=true;
            app.current_trait.id = id;
            app.current_trait.min_value = tc.min_value;
            app.current_trait.max_value = tc.max_value;
            app.current_trait.trait = tc.trait;
            app.current_trait.include_if_in_range = tc.include_if_in_range;

            app.updateTraitModal.show();
            app.clearMainFormErrors();
        },

        getTraitById: function getTraitById(id){
            for(let i=0; i<app.recruitment_params.trait_constraints.length; i++)
            {
                if(app.recruitment_params.trait_constraints[i].id == id){
                    return app.recruitment_params.trait_constraints[i];
                }
            }

            return null;
        },

        //fire when edit experiment model hides, cancel action if nessicary
        hideUpdateTrait:function hideUpdateTrait(){
            if(app.cancelModal)
            {
               
            }
        },

    },

    //run when vue is mounted
    mounted(){
        Vue.nextTick(() => {
            app.loading = false;

            app.editTraitsModal = bootstrap.Modal.getOrCreateInstance(document.getElementById('editTraitsModal'), {keyboard: false});
            app.updateTraitModal = bootstrap.Modal.getOrCreateInstance(document.getElementById('updateTraitModal'), {keyboard: false});
        });
    
    },                 

}).mount('#app');


