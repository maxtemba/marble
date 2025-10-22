module hello(
    input wire clk, 
    input wire rst,
    output reg [31:0] counter
    );
    
    always @(posedge clk)
    begin
        if (rst)
            counter <= 0;
        else
            counter <= counter + 1;
    end

endmodule