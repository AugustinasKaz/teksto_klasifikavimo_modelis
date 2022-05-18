let recreate_table = false

window.addEventListener("load", function () {
    const modal = document.getElementById("myModal");
    const modal_table = document.getElementById("modal_table");

    let row11 = modal_table.insertRow(0);
    let cell11 = row11.insertCell(0);
    let cell22 = row11.insertCell(1);
    let cell33 = row11.insertCell(2);

    //modal table header
    let header1 = modal_table.createTHead();
    header1.setAttribute("id", "test");
    let row1 = header1.insertRow(0);    
    let cell_1 = row1.insertCell(0);
    let cell_2 = row1.insertCell(1);
    let cell_3 = row1.insertCell(2);
    cell_1.innerHTML = "<h4>Source Port</h4>"; 
    cell_2.innerHTML = "<h4>Destination Port</h4>"; 
    cell_3.innerHTML = "<h4>Prediction accuracy</h4>"; 

    window.onclick = function(event) {
        if (event.target == modal) {
          modal.style.display = "none";
        }
    } 

    function show_modal(event){
        let data_obj = event.currentTarget.data
        cell11.innerHTML = data_obj['src_port'];
        cell22.innerHTML = data_obj['dst_port'];
        cell33.innerHTML = data_obj['prediction'][1];
        modal.style.display = "block";
    }

    let request = new XMLHttpRequest();
    request.open("GET", 'https://packets-bucket-web.s3.amazonaws.com/web_display/data.json', false);
    request.setRequestHeader('Access-Control-Allow-Origin', '*');
    request.send(null)
    const packets_list = JSON.parse(request.response);

    
    create_table(packets_list,show_modal)
    create_select_options(packets_list, show_modal)
})

function create_new_packet_list(packets_list, filter1,filter2,filter3){
    let new_list = packets_list.filter(function(elem){
        time_split = elem['timestamp'].split(" "); 
        tmp_str = elem['prediction'][0].toString().substring(9,17);
        console.log(tmp_str)
        return time_split[0] == filter1 && elem['src_ip'] == filter2 && tmp_str == filter3 })

    return new_list
}



function create_table(packets_list,show_modal){
    let table = document.getElementById("packets_table");
    if(recreate_table == true){
        while(table.firstElementChild) {
            table.firstElementChild.remove();
        }
        recreate_table = false
    }

    //table data
    packets_list.forEach(elem => {
        time_split = elem['timestamp'].split(" ");
        let row = table.insertRow(0);
        row.data = elem;
        row.addEventListener("click", show_modal);
        let cell1 = row.insertCell(0);
        let cell2 = row.insertCell(1);
        let cell3 = row.insertCell(2);
        let cell4 = row.insertCell(3);
        let cell5 = row.insertCell(4);
        cell1.innerHTML = time_split[0];
        cell2.innerHTML = time_split[1]; 
        cell3.innerHTML = elem['src_ip'];
        cell4.innerHTML = elem['dst_ip'];
        let tmp_str = elem['prediction'][0];
        cell5.innerHTML = tmp_str.toString().substring(9,17);
    });

        //table header
        let header = table.createTHead();
        header.setAttribute("id", "test");
        let row = header.insertRow(0);    
        let cell1 = row.insertCell(0);
        let cell2 = row.insertCell(1);
        let cell3 = row.insertCell(2);
        let cell4 = row.insertCell(3);
        let cell5 = row.insertCell(4);
        cell1.innerHTML = "<h4>Date</h4>"; 
        cell2.innerHTML = "<h4>Time</h4>"; 
        cell3.innerHTML = "<h4>Source IP</h4>"; 
        cell4.innerHTML = "<h4>Destination IP</h4>"; 
        cell5.innerHTML = "<h4>Status</h4>"; 
}



function create_select_options(packets_list, show_modal){
    let uni_scr_ip = []
    let uni_dates = []
    const uni_status = ['Secure', 'Insecure']
    packets_list.forEach(elem => {
        uni_dates.push(time_split[0])
        uni_scr_ip.push(elem['src_ip'])
    })
    let date_select = document.getElementById("date_filter");
    let ip_select = document.getElementById("ip_filter");
    let status_select = document.getElementById("status_filter");
    uni_scr_ip = [... new Set(uni_scr_ip)]
    uni_dates = [... new Set(uni_dates)]

    uni_dates.forEach(date => {
        let opt = document.createElement('option');
        opt.value = date;
        opt.innerHTML = date;
        date_select.appendChild(opt);
    })

    uni_scr_ip.forEach(ip => {
        let opt = document.createElement('option');
        opt.value = ip;
        opt.innerHTML = ip;
        ip_select.appendChild(opt);
    })

    uni_status.forEach(ip => {
        let opt = document.createElement('option');
        opt.value = ip;
        opt.innerHTML = ip;
        status_select.appendChild(opt);
    })

    let btn = document.getElementById("filter_btn");
    btn.addEventListener("click", function(){
        filter1 = date_select.options[ date_select.selectedIndex ].value
        filter2 = ip_select.options[ ip_select.selectedIndex ].value
        filter3 = status_select.options[ status_select.selectedIndex ].value
        new_list = create_new_packet_list(packets_list, filter1,filter2,filter3);
        recreate_table = true
        create_table(new_list, show_modal)
    });
}
