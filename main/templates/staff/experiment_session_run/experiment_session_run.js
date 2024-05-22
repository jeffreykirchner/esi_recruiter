"use strict";
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

let app = Vue.createApp({

    delimiters: ['[[', ']]'],
       
    data(){return{
        sessionDay:{{sessionDay_json|safe}},
        bumpButtonText : '<i class="fas fa-arrow-left"></i> Bump',
        noShowButtonText : '<i class="fas fa-arrow-left"></i> No Show',
        attendButtonText : '<i class="fas fa-arrow-left"></i> Attend',
        waitButtonText : '<i class="fas fa-spinner fa-spin"></i>',
        dateText:'<i class="fa fa-spinner fa-spin" aria-hidden="true"></i>',
        saveButtonText: 'Save Payouts <i class="far fa-save" aria-hidden="true"></i>',
        fillShowUpFeeButtonText : "Fill Bonus: $",
        completeSessionButtonText : 'Complete Session <i class="fas fa-check"></i>',
        openSessionButtonText : 'Re-Open Session <i class="fas fa-book-open"></i>',
        bumpAllButtonText : 'Bump All <i class="fas fa-user-slash"></i>',
        autoBumpButtonText : 'Auto Bump <i class="fa fa-random" aria-hidden="true"></i>',
        printPayoutsButtonText : 'Print Attendees <i class="fas fa-print"></i>',
        printBumpsButtonText : 'Print Bumps <i class="fas fa-print"></i>',
        paypalExportButtonText : 'Paypal Export <i class="fab fa-paypal"></i>',
        paypalDirectButtonText : 'Paypal Direct <i class="fab fa-paypal"></i>',
        earningsExportButtonText : 'Attended Export <i class="fas fa-download"></i>',
        roundUpButtonText : 'Round Earnings <i class="fas fa-circle-notch"></i>',
        fillEarningsWithFixedButtonText : 'Fill',
        updatePayoutsRequired : false,             //need to send payouts update
        updatingPayoutsInProgress : false,         //currently sending a payouts update
        payoutTotal:"",                            //total paid to subjects
        fillEarningsWithValue:"",                   //amount to fill all earnings with
        isAdmin:{%if user.is_staff%}true{%else%}false{%endif%},  
        stripeReaderSpinner : "",
        stripeReaderValue : "",
        stripeReaderStatus : "",
        autoAddUsers :false,                         //automatically add users if they are not checked in
        ignoreConstraints:false,                    //ignore recruitment constraints and add user
        upload_file : null,
        upload_file_name:'Choose File',
        uploadEarningsButtonText:'Upload File <i class="fas fa-upload"></i>',            //upload earnings file button
        uploadEarningsMessage:'',                                                        //upload earnings response message
        uploadEarningsTextBoxButtonText:'Upload Earnings <i class="fas fa-upload"></i>',     //upload earnings text button
        uploadEarningsText:'',                                                           //upload earnings text 
        uploadIdType:'student_id',
        noticeHeader : "PayPal Direct Payments",
        noticeBody : "",
        auto_add_users_on_upload : false,  

        //modals
        uploadEarningsModal : null,
        noticeModal : null,
    }},

    methods:{
        //get the session day json info
        getSession:function getSession(){
            axios.post('/experimentSessionRun/{{id}}/', {
                    action :"getSession" ,                                                                                                                             
                })
                .then(function (response) {     
                    app.sessionDay= response.data.sessionDay; 
                    app.calcPayoutTotal();      

                    app.dateText = app.sessionDay.date;      
                    app.dateText += ", " + app.sessionDay.length + " Minutes";
                    app.dateText += ", " + app.sessionDay.location.name;    
                    
                    app.fillShowUpFeeButtonText += app.sessionDay.defaultShowUpFee;

                })
                .catch(function (error) {
                    console.log(error);                                   
                });                        
            },

        //stripe reader checkin
        stripeReaderCheckin:function stripeReaderCheckin(){
            window.setTimeout(app.stripeReaderCheckin, 250);
            
            if(app.stripeReaderValue == "") return;
            if(app.stripeReaderSpinner != "") return;
            if(!app.stripeReaderValue.includes("=")) return;

            app.stripeReaderSpinner = '<i class="fas fa-spinner fa-spin"></i>';
            app.stripeReaderStatus="";

            axios.post('/experimentSessionRun/{{id}}/', {
                        action :"stripeReaderCheckin" ,
                        value:app.stripeReaderValue,    
                        autoAddUsers:app.autoAddUsers,   
                        ignoreConstraints:app.ignoreConstraints,                                                                                                                        
                    })
                .then(function (response) {                                
                    app.sessionDay = response.data.sessionDay;   
                    app.stripeReaderSpinner = "";   
                    app.stripeReaderValue = "";    
                    app.stripeReaderStatus = response.data.status.message;

                    let ids = response.data.status.info;
                    for(let i=0;i<ids.length;i++)
                    {
                        app.stripeReaderStatus += " <a href='/userInfo/" + ids[i] + "/' target='_blank' >view</a>";
                    }

                    })
                .catch(function (error) {
                    console.log(error);                                   
                });
        },

        //export a csv file for paypal mass payment
        payPalExport:function payPalExport(){
            if(app.saveButtonText.indexOf("*") >= 0)
            {   
                alert("Save payouts before continuing.") ;                    
                return;                        
            }
            
            app.paypalExportButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            
            axios.post('/experimentSessionRun/{{id}}/', {
                        action :"payPalExport" ,                                                                                                                                                      
                    })
                    .then(function (response) {      
                    
                    // let csvContent = "data:text/csv;charset=utf-8,";
                    // csvContent = response

                    console.log(response)

                    let downloadLink = document.createElement("a");
                    let blob = new Blob(["\ufeff", response.data]);
                    let url = URL.createObjectURL(blob);
                    downloadLink.href = url;
                    downloadLink.download = "PayPal_Mass_Pay_" + app.sessionDay.id + ".csv";

                    document.body.appendChild(downloadLink);
                    downloadLink.click();
                    document.body.removeChild(downloadLink);

                    app.paypalExportButtonText = 'Paypal Export <i class="fab fa-paypal"></i>';                  
                    })
                    .catch(function (error) {
                        console.log(error);                                   
                    });
        },

        //export an earnings csv file 
        earningsExport:function earningsExport(){
            if(app.saveButtonText.indexOf("*") >= 0)
            {   
                confirm("Save payouts before continuing.") ;                    
                return;                        
            }
            
            app.earningsExportButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            
            axios.post('/experimentSessionRun/{{id}}/', {
                        action :"getEarningsExport" ,                                                                                                                                                      
                    })
                    .then(function (response) {      
                    
                    // let csvContent = "data:text/csv;charset=utf-8,";
                    // csvContent = response

                    console.log(response)

                    let downloadLink = document.createElement("a");
                    let blob = new Blob(["\ufeff", response.data]);
                    let url = URL.createObjectURL(blob);
                    downloadLink.href = url;
                    downloadLink.download = "Attending_Export_" + app.sessionDay.id + ".csv";

                    document.body.appendChild(downloadLink);
                    downloadLink.click();
                    document.body.removeChild(downloadLink);

                    app.earningsExportButtonText = 'Attended Export <i class="fas fa-download"></i>';                  
                    })
                    .catch(function (error) {
                        console.log(error);                                   
                    });
        },

        //randomly bump excess subjects
        autobump:function autobump(){
            app.autoBumpButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            
            // esdu.buttonText = '<i class="fas fa-spinner fa-spin"></i>'
                axios.post('/experimentSessionRun/{{id}}/', {
                        action :"autoBump" ,   
                                                                                                                                            
                    })
                    .then(function (response) {                                
                    app.sessionDay = response.data.sessionDay;    

                    app.autoBumpButtonText = 'Auto Bump <i class="fa fa-random" aria-hidden="true"></i>';                    
                    })
                    .catch(function (error) {
                        console.log(error);                                   
                    });                        
        },
        
        //set subject to attended
        attendSubject:function attendSubject(esduID,id){
            app.sessionDay.experiment_session_days_user[id].waiting = true;
            
            // esdu.buttonText = '<i class="fas fa-spinner fa-spin"></i>'
            axios.post('/experimentSessionRun/{{id}}/', {
                    action :"attendSubject" ,   
                    id:esduID, 
                    localId:id,                                                                                                                         
                })
                .then(function (response) {                                
                    app.sessionDay = response.data.sessionDay;     
                    app.stripeReaderStatus= response.data.status;                   
                })
                .catch(function (error) {
                    console.log(error);                                   
                });                        
            },

        //set subject to bumped
        bumpSubject:function bumpSubject(esduID,id){
            app.sessionDay.experiment_session_days_user[id].waiting = true;

            axios.post('/experimentSessionRun/{{id}}/', {
                    action :"bumpSubject" ,   
                    id:esduID,                                                                                                            
                })
                .then(function (response) {     
                    app.sessionDay = response.data.sessionDay;  
                    app.stripeReaderStatus= response.data.statusMessage;                                                               
                })
                .catch(function (error) {
                    console.log(error);                                   
                });                        
            },
        
        //set subject to no show
        noShowSubject:function noShowSubject(esduID,id){
            app.sessionDay.experiment_session_days_user[id].waiting = true;
            
            axios.post('/experimentSessionRun/{{id}}/', {
                    action :"noShowSubject" , 
                    id:esduID,                                                                                                                            
                })
                .then(function (response) {     
                    app.sessionDay = response.data.sessionDay;    
                    app.stripeReaderStatus = "";                                                                  
                })
                .catch(function (error) {
                    console.log(error);                                   
                });                        
            },
        
        //save the current payouts
        savePayouts:function savePayouts(){
            app.saveButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/experimentSessionRun/{{id}}/', {
                    action :"savePayouts" ,  
                    payoutList : app.getPayoutlist(),                                                                                                                           
                })
                .then(function (response) {     
                    app.sessionDay= response.data.sessionDay;      
                    app.saveButtonText = 'Save Payouts <i class="far fa-save" aria-hidden="true"></i>';
                    app.calcPayoutTotal();
                })
                .catch(function (error) {
                    console.log(error);                                   
                });
        },

        //finsh session, prevents further editing
        completeSession:function completeSession(){

            if(app.saveButtonText.indexOf("*") >= 0)
            {   
                confirm("Save payouts before continuing.") ;                    
                return;                        
            }

            app.completeSessionButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            app.openSessionButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/experimentSessionRun/{{id}}/', {
                    action :"completeSession" ,                                                                                                                             
                })
                .then(function (response) {     
                    app.sessionDay = response.data.sessionDay;     
                    
                    app.completeSessionButtonText = 'Complete Session <i class="fas fa-check"></i>';
                    app.openSessionButtonText = 'Re-Open Session <i class="fas fa-book-open"></i>';
                })
                .catch(function (error) {
                    console.log(error);                                   
                });
        },

        //calc payout total of visible subjects
        calcPayoutTotal:function calcPayoutTotal(){
            let s = 0;

            for(let i=0;i<app.sessionDay.experiment_session_days_user.length;i++)
            {
                let u = app.sessionDay.experiment_session_days_user[i];

                if(u.show)
                {
                    s += parseFloat(u.payout);                              
                }
            }

            app.payoutTotal = s.toFixed(2);
        },

        //fill subjects with default show up fee from experiments model
        fillWithDefaultShowUpFee:function fillWithDefaultShowUpFee(){
            app.fillShowUpFeeButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/experimentSessionRun/{{id}}/', {
                    action :"fillDefaultShowUpFee" ,                                                                                                                             
                })
                .then(function (response) {     
                    app.sessionDay = response.data.sessionDay;   
                    app.fillShowUpFeeButtonText = "Fill Bonus: $" + app.sessionDay.defaultShowUpFee; 
                    app.calcPayoutTotal();                     
                })
                .catch(function (error) {
                    console.log(error);                                   
                });
        },

        //fill subjects with default show up fee from experiments model
        fillEarningsWithFixed:function fillEarningsWithFixed(){

            if(app.fillEarningsWithValue=="") return;

            app.fillEarningsWithFixedButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/experimentSessionRun/{{id}}/', {
                    action :"fillEarningsWithFixed" ,
                    amount: app.fillEarningsWithValue,                                                                                                                             
                })
                .then(function (response) {     
                    app.sessionDay = response.data.sessionDay;    
                    app.fillEarningsWithFixedButtonText = "Fill";
                    app.fillEarningsWithValue="";    
                    app.calcPayoutTotal();                          
                })
                .catch(function (error) {
                    console.log(error);                                   
                });
        },

        //run when key pressed in payouts box
        payoutsKeyUp:function payoutsKeyUp(userId,localId){
            app.saveButtonText = 'Save Payouts <i class="far fa-save" aria-hidden="true"></i> *';
        },

        //when user changes the payouts, auto save
        payoutsChange:function payoutsChange(userId,localId){
            app.saveButtonText = 'Save Payouts <i class="far fa-save" aria-hidden="true"></i> *';
            
            if(app.updatingPayoutsInProgress)
            {
                app.updatePayoutsRequired = true;
                return;
            }
            else
            {
                app.updatePayoutsRequired = false;
                app.updatingPayoutsInProgress = true;
            }                  
            
            axios.post('/experimentSessionRun/{{id}}/', {
                    action :"backgroundSave", 
                    payoutList : app.getPayoutlist(),                                                                                                                    
                })
                .then(function (response) {     
                    status = response.data.status;    

                    if(status == "success")
                    {
                        app.updatingPayoutsInProgress = false;
                    }
                    else
                    {

                    }

                    if(app.updatePayoutsRequired){
                        app.payoutsChange(userId,localId); 
                    }
                })
                .catch(function (error) {
                    console.log(error);                                   
                });
        },   

        //return a list of the payouts entered by the user
        getPayoutlist:function getPayoutlist(){
            let payoutList=[];

            for(let i=0;i<app.sessionDay.experiment_session_days_user.length;i++)
            {
                let tempU = app.sessionDay.experiment_session_days_user[i];

                let tempV = {"id":tempU.id,
                        "earnings":tempU.earnings,
                        "showUpFee":tempU.show_up_fee,
                        }
                payoutList.push(tempV);
            }

            return payoutList;
        },             

        //bump all present users
        bumpAll:function bumpAll(){
            app.bumpAllButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/experimentSessionRun/{{id}}/', {
                    action :"bumpAll"                                                                                                                            
                })
                .then(function (response) {     
                    app.sessionDay= response.data.sessionDay;      
                    app.bumpAllButtonText = 'Bump All <i class="fas fa-user-slash"></i>';
                })
                .catch(function (error) {
                    console.log(error);                                   
                });
        },

        //print payouts
        printPayouts:function printPayouts(){
            if(app.saveButtonText.indexOf("*") >= 0)
            {   
                alert("Save payouts before continuing.") ;                    
                return;                        
            }

            window.open('/experimentSessionPayouts/' + app.sessionDay.id +'/payouts/', '_blank');
        },

        //print bumps
        printBumps:function printBumps(){
            if(app.saveButtonText.indexOf("*") >= 0)
            {  
                alert("Save payouts before continuing.") ;                      
                return;                        
            }

            window.open('/experimentSessionPayouts/' + app.sessionDay.id +'/bumps/', '_blank');
        },

        //open traits for attended subjects
        openTraits:function openTraits(id){
            window.open('/traits/?SESSION_DAY_ID=' + id, '_blank')
        },

        //upload earings file csv
        uploadEarnings:function uploadEarnings(){

            if(app.upload_file == null)
                return;

            app.uploadEarningsMessage = "";
            app.uploadEarningsButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            let formData = new FormData();
            formData.append('file', app.upload_file);
            formData.append('auto_add', app.auto_add_users_on_upload);

            axios.post('/experimentSessionRun/{{id}}/', formData,
                    {
                        headers: {
                            'Content-Type': 'multipart/form-data'
                            }
                        } 
                    )
                    .then(function (response) {     

                        app.uploadEarningsMessage = response.data.message;

                        app.uploadEarningsButtonText= 'Upload File <i class="fas fa-upload"></i>';
                        app.sessionDay = response.data.sessionDay;   
                        app.calcPayoutTotal();                                                                             
                    })
                    .catch(function (error) {
                        console.log(error);
                        app.searching=false;
                    });                        
                },
        
        //upload earings text csv format
        uploadEarningsTextJS:function uploadEarningsTextJS(){

            if(app.uploadEarningsText == "")
                return;

            app.uploadEarningsMessage = "";
            app.uploadEarningsTextBoxButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/experimentSessionRun/{{id}}/', {
                        action : "uploadEarningsText",
                        text : app.uploadEarningsText,         
                        autoAddUsers : app.auto_add_users_on_upload, 
                        uploadIdType : app.uploadIdType,                                                                                                            
                    })
                    .then(function (response) {     

                        app.uploadEarningsMessage = response.data.message;

                        app.uploadEarningsTextBoxButtonText= 'Upload Earnings <i class="fas fa-upload"></i>';
                        app.sessionDay = response.data.sessionDay;   
                        app.calcPayoutTotal();     

                    })
                    .catch(function (error) {
                        console.log(error);
                        app.searching=false;
                    });                        
                },

        //store the location of the file to be uploaded
        handleFileUpload:function handleFileUpload(){
            app.upload_file = app.$refs.file.files[0];

            app.upload_file_name = app.upload_file.name;

            let reader = new FileReader();
            reader.onload = e => app.uploadEarningsText = e.target.result;
            reader.readAsText(app.upload_file);

        },

        //fire when show upload earnings
        showUploadEarnings:function showUploadEarnings(){
            app.uploadEarningsMessage = "";
            app.uploadEarningsModal.show();
        },

        hideUploadEarnings:function hideUploadEarnings(){
        },
        
        //fill subjects with default show up fee from experiments model
        roundEarningsUp:function roundEarningsUp(){

            if(app.saveButtonText.indexOf("*") >= 0)
            {   
                alert("Save payouts before continuing.") ;                    
                return;                        
            }

            app.roundUpButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/experimentSessionRun/{{id}}/', {
                    action :"roundEarningsUp",                                                                                                                           
                })
                .then(function (response) {     
                    app.sessionDay = response.data.sessionDay;    
                    app.roundUpButtonText = 'Round Earnings <i class="fas fa-circle-notch"></i>';   
                    app.calcPayoutTotal();                       
                })
                .catch(function (error) {
                    console.log(error);                                   
                });
        },

        //pay subjects with PayPal API
        payPalAPI:function payPalAPI(){
            if(app.sessionDay.experiment_session_days_user.length == 0)
            {
                alert("No subjects in session.") ; 
                return;
            }

            if(app.payoutTotal == "0.00")
            {
                alert("No payouts entered.") ; 
                return;
            }

            if(app.saveButtonText.indexOf("*") >= 0)
            {   
                alert("Save payouts before continuing.") ;                    
                return;                        
            }

            let r = confirm("Pay subjects directly with PayPal's API?");

            if (r == false)
            {
                return;
            }           


            app.paypalDirectButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/experimentSessionRun/{{id}}/', {
                    action :"payPalAPI",                                                                                                                           
                })
                .then(function (response) {     
                    
                    app.sessionDay = response.data.sessionDay;
                    app.paypalDirectButtonText = 'Paypal Direct <i class="fab fa-paypal"></i>';           
                    
                    if( response.data.error_message != "")
                    {
                        app.noticeBody = response.data.error_message;
                    }
                    else
                    {
                        app.noticeBody = response.data.result;
                    }

                    app.noticeModal.show();
                })
                .catch(function (error) {
                    console.log(error);                                   
                });
        },

        //format date to human readable
        formatDate: function formatDate(value){
            if (value) {        
                //console.log(value);                    
                return moment(String(value)).local().format('MM/DD/YYYY hh:mm a');
            }
            else{
                return "date format error";
            }
        },
    },

    mounted(){
                  
        Vue.nextTick(() => {
            app.getSession();       
            window.setTimeout(app.stripeReaderCheckin, 250);
            app.uploadEarningsModal = bootstrap.Modal.getOrCreateInstance(document.getElementById('uploadEarningsModal'), {keyboard: false});
            app.noticeModal = bootstrap.Modal.getOrCreateInstance(document.getElementById('noticeModal'), {keyboard: false});

            document.getElementById('uploadEarningsModal').addEventListener('hidden.bs.modal', app.hideUploadEarnings);
        })
    
    },
}).mount('#app');